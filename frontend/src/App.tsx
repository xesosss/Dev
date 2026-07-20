import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  CreditCard,
  Package,
  RefreshCw,
  ShoppingCart,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { createOrder, getHealth, listOrders, listProducts, payOrder } from "./api";
import type { HealthResponse, Order, Product } from "./types";

type LoadState = "idle" | "loading" | "ready" | "error";

function currency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedSku, setSelectedSku] = useState("coffee-001");
  const [quantity, setQuantity] = useState(1);
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [message, setMessage] = useState<string | null>(null);

  const selectedProduct = useMemo(
    () => products.find((product) => product.sku === selectedSku),
    [products, selectedSku],
  );

  const pendingOrders = orders.filter((order) => order.status === "pending");
  const paidRevenue = orders
    .filter((order) => order.status === "paid")
    .reduce((total, order) => total + order.total, 0);

  async function refreshData() {
    setLoadState("loading");
    setMessage(null);

    try {
      const [healthResult, productsResult, ordersResult] = await Promise.all([
        getHealth(),
        listProducts(),
        listOrders(),
      ]);

      setHealth(healthResult);
      setProducts(productsResult);
      setOrders(ordersResult);
      setSelectedSku((currentSku) => productsResult.find((item) => item.sku === currentSku)?.sku ?? productsResult[0]?.sku ?? "");
      setLoadState("ready");
    } catch (error) {
      setLoadState("error");
      setMessage(error instanceof Error ? error.message : "Request failed");
    }
  }

  async function handleCreateOrder() {
    if (!selectedProduct) {
      return;
    }

    setMessage(null);
    try {
      const order = await createOrder(selectedProduct.sku, quantity);
      setMessage(`Order ${order.id.slice(0, 8)} created`);
      await refreshData();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Order failed");
    }
  }

  async function handlePayOrder(orderId: string) {
    setMessage(null);
    try {
      await payOrder(orderId);
      await refreshData();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Payment failed");
    }
  }

  useEffect(() => {
    void refreshData();
  }, []);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <span className="eyebrow">Observable Shop</span>
          <h1>Operations Console</h1>
        </div>
        <div className={`status-pill ${loadState === "error" ? "status-error" : "status-ok"}`}>
          {loadState === "error" ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}
          <span>{health ? `${health.service} / ${health.environment}` : "API pending"}</span>
        </div>
      </header>

      <section className="summary-grid" aria-label="Shop summary">
        <div className="metric-block">
          <Activity size={20} />
          <span className="metric-value">{orders.length}</span>
          <span className="metric-label">orders</span>
        </div>
        <div className="metric-block">
          <ShoppingCart size={20} />
          <span className="metric-value">{pendingOrders.length}</span>
          <span className="metric-label">pending</span>
        </div>
        <div className="metric-block">
          <CreditCard size={20} />
          <span className="metric-value">{currency(paidRevenue)}</span>
          <span className="metric-label">paid</span>
        </div>
      </section>

      <section className="workspace-grid">
        <div className="panel">
          <div className="panel-heading">
            <div>
              <h2>Products</h2>
              <p>{products.length} active SKUs</p>
            </div>
            <button className="icon-button" onClick={refreshData} type="button" title="Refresh data">
              <RefreshCw size={18} />
            </button>
          </div>

          <div className="product-list">
            {products.map((product) => (
              <button
                className={`product-row ${selectedSku === product.sku ? "selected" : ""}`}
                key={product.sku}
                onClick={() => setSelectedSku(product.sku)}
                type="button"
              >
                <Package size={18} />
                <span>
                  <strong>{product.name}</strong>
                  <small>{product.sku}</small>
                </span>
                <span className="price">{currency(product.price)}</span>
                <span className="stock">{product.in_stock}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="panel order-panel">
          <div className="panel-heading">
            <div>
              <h2>New Order</h2>
              <p>{selectedProduct?.name ?? "No product selected"}</p>
            </div>
          </div>

          <label className="field">
            <span>Quantity</span>
            <input
              min="1"
              max="20"
              type="number"
              value={quantity}
              onChange={(event) => setQuantity(Number(event.target.value))}
            />
          </label>

          <div className="quote">
            <span>Total</span>
            <strong>{currency((selectedProduct?.price ?? 0) * quantity)}</strong>
          </div>

          <button className="primary-button" onClick={handleCreateOrder} type="button">
            <ShoppingCart size={18} />
            <span>Create Order</span>
          </button>

          {message && (
            <div className={`message ${loadState === "error" ? "message-error" : ""}`}>{message}</div>
          )}
        </div>

        <div className="panel orders-panel">
          <div className="panel-heading">
            <div>
              <h2>Orders</h2>
              <p>{pendingOrders.length} awaiting payment</p>
            </div>
          </div>

          <div className="orders-list">
            {orders.length === 0 ? (
              <div className="empty-state">No orders yet</div>
            ) : (
              orders.map((order) => (
                <div className="order-row" key={order.id}>
                  <span>
                    <strong>{order.id.slice(0, 8)}</strong>
                    <small>
                      {order.quantity} x {order.sku}
                    </small>
                  </span>
                  <span className={`order-status ${order.status}`}>{order.status}</span>
                  <span className="price">{currency(order.total)}</span>
                  <button
                    className="icon-button"
                    disabled={order.status !== "pending"}
                    onClick={() => handlePayOrder(order.id)}
                    type="button"
                    title="Mark as paid"
                  >
                    <CreditCard size={18} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </section>
    </main>
  );
}

export default App;

