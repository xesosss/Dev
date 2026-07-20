export type HealthResponse = {
  status: string;
  service: string;
  environment: string;
};

export type Product = {
  sku: string;
  name: string;
  price: number;
  in_stock: number;
};

export type OrderStatus = "pending" | "paid" | "cancelled";

export type Order = {
  id: string;
  sku: string;
  quantity: number;
  total: number;
  status: OrderStatus;
};

