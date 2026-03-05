import React from "react";
import { createRoot } from "react-dom/client";
import { ConfigProvider } from "antd";

import App from "./App";
import "./styles/global.css";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: "#0d8a72",
          borderRadius: 14,
          fontFamily: "Space Grotesk, IBM Plex Sans, sans-serif",
        },
      }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>
);
