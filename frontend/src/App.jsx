import { Button, Card, Segmented } from "antd";
import { useMemo, useState } from "react";

import LogsPage from "./pages/LogsPage";
import LoginPage from "./pages/LoginPage";
import PushPage from "./pages/PushPage";
import RssPage from "./pages/RssPage";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [tab, setTab] = useState("rss");

  const content = useMemo(() => {
    if (tab === "rss") return <RssPage />;
    if (tab === "push") return <PushPage />;
    return <LogsPage />;
  }, [tab]);

  if (!token) {
    return <LoginPage onLogin={() => setToken(localStorage.getItem("token"))} />;
  }

  return (
    <div className="shell">
      <div className="title-wrap">
        <h1 className="title">Sci2Email Control Center</h1>
        <div className="subtitle">RSS 订阅、精细推送与运行监控</div>
      </div>

      <Card className="glass" style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <Segmented
            value={tab}
            onChange={setTab}
            options={[
              { label: "RSS 管理", value: "rss" },
              { label: "推送管理", value: "push" },
              { label: "日志中心", value: "logs" },
            ]}
          />
          <Button
            onClick={() => {
              localStorage.removeItem("token");
              setToken("");
            }}
          >
            退出登录
          </Button>
        </div>
      </Card>

      {content}
    </div>
  );
}
