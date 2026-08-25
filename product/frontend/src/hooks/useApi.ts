import { useEffect, useState } from "react";
import { getApiErrorMessage } from "../services/api";

interface AsyncState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

/**
 * Small data-fetching hook shared by every page.
 *
 * Pass a stable fetcher (e.g. `api.fetchHealth`). The effect re-runs only
 * when the fetcher identity changes. Errors are normalized through the API
 * error abstraction so pages always render user-safe messages.
 */
export function useApi<T>(fn: () => Promise<T>) {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    let cancelled = false;
    fn()
      .then((data) => {
        if (!cancelled) setState({ data, error: null, loading: false });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            data: null,
            error: getApiErrorMessage(err),
            loading: false,
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [fn]);

  return state;
}
