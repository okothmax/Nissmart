import useSWR from "swr";

import { apiFetch } from "./api";

const jsonFetcher = async <T,>(endpoint: string): Promise<T> => {
  const { data } = await apiFetch<T>(endpoint);
  return data;
};

export function useApi<T>(
  endpoint: string | null,
  options?: { revalidateOnFocus?: boolean }
) {
  return useSWR<T>(endpoint, endpoint ? jsonFetcher<T> : null, {
    revalidateOnFocus: options?.revalidateOnFocus ?? false,
  });
}
