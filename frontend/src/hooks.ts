import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import type { Me } from "./types";

export const useMe = () =>
  useQuery({ queryKey: ["me"], queryFn: () => api<Me>("/me"), retry: false, staleTime: 60_000 });

export function useCoords() {
  const key = "pickup.coords";
  const read = (): { lat: number; lng: number } | null => {
    try {
      return JSON.parse(sessionStorage.getItem(key) ?? "null");
    } catch {
      return null;
    }
  };
  const ask = (done: () => void) =>
    navigator.geolocation?.getCurrentPosition((p) => {
      sessionStorage.setItem(key, JSON.stringify({ lat: p.coords.latitude, lng: p.coords.longitude }));
      done();
    });
  return { coords: read(), ask };
}
