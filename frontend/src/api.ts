import type { HealthResponse, Order, Product } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorBody.detail ?? response.statusText);
  }

  return response.json() as Promise<T>;
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health/ready");
}

export function listProducts(): Promise<Product[]> {
  return request<Product[]>("/products");
}

export function listOrders(): Promise<Order[]> {
  return request<Order[]>("/orders");
}

export function createOrder(sku: string, quantity: number): Promise<Order> {
  return request<Order>("/orders", {
    method: "POST",
    body: JSON.stringify({ sku, quantity }),
  });
}

export function payOrder(orderId: string): Promise<Order> {
  return request<Order>(`/orders/${orderId}/pay`, { method: "POST" });
}

