"use client";

import { useState, useEffect } from "react";
import { SectionCard } from "@/components/SectionCard";
import { getApiKeyStatus, saveApiKey, deleteApiKey, testApiKey, ApiKeyStatus } from "@/lib/api";
import { StudentShellClient } from "@/components/StudentShellClient";

type AuthMode = "qianfan" | "aistudio";

export default function StudentSettingsPage() {
  const [authMode, setAuthMode] = useState<AuthMode>("qianfan");
  const [apiKey, setApiKey] = useState("");
  const [secretKey, setSecretKey] = useState("");
  const [status, setStatus] = useState<ApiKeyStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState<"success" | "error" | "info">("info");
  const [showKey, setShowKey] = useState(false);

  useEffect(() => {
    getApiKeyStatus()
      .then((data) => {
        setStatus(data);
        if (data.auth_mode === "aistudio" || data.auth_mode === "qianfan") {
          setAuthMode(data.auth_mode);
        }
      })
      .catch(() => setMessage("无法连接后端，请确认后端已启动"))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!apiKey.trim()) {
      setMessage("请填写 API Key");
      setMessageType("error");
      return;
    }
    if (authMode === "qianfan" && !secretKey.trim()) {
      setMessage("千帆模式需要同时填写 Secret Key");
      setMessageType("error");
      return;
    }
    setSaving(true);
    setMessage("");
    try {
      const result = await saveApiKey({
        api_key: apiKey.trim(),
        secret_key: authMode === "qianfan" ? secretKey.trim() : undefined,
        auth_mode: authMode,
      });
      setStatus(result);
      setMessage("保存成功，AI 模型已就绪");
      setMessageType("success");
      setApiKey("");
      setSecretKey("");
    } catch {
      setMessage("保存失败，请检查后端连接或登录状态");
      setMessageType("error");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setSaving(true);
    setMessage("");
    try {
      const result = await deleteApiKey();
      setStatus(result);
      setMessage("密钥已删除");
      setMessageType("info");
    } catch {
      setMessage("删除失败");
      setMessageType("error");
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setMessage("");
    try {
      const result = await testApiKey();
      if (result.success) {
        setMessage(result.message);
        setMessageType("success");
      } else {
        setMessage(result.message);
        setMessageType("error");
      }
    } catch {
      setMessage("验证请求失败，请检查后端连接");
      setMessageType("error");
    } finally {
      setTesting(false);
    }
  };

  const handleModeSwitch = (mode: AuthMode) => {
    setAuthMode(mode);
    setApiKey("");
    setSecretKey("");
    setMessage("");
  };

  const infoByMode: Record<AuthMode, { title: string; desc: string; link: string; linkText: string; apiHint: string }> = {
    qianfan: {
      title: "百度千帆 V2（推荐）",
      desc: "使用百度智能云千帆平台的 API Key 和 Secret Key 进行 OAuth2 认证，支持最新模型。",
      link: "https://console.bce.baidu.com/qianfan/",
      linkText: "百度智能云千帆控制台",
      apiHint: "调用地址: https://qianfan.baidubce.com/v2/chat/completions",
    },
    aistudio: {
      title: "百度 AI Studio（旧版）",
      desc: "使用百度 AI Studio 的 API Key，通过 OpenAI 兼容接口调用。",
      link: "https://aistudio.baidu.com",
      linkText: "百度 AI Studio",
      apiHint: "调用地址: https://aistudio.baidu.com/llm/lmapi/v3",
    },
  };

  const currentModeInfo = infoByMode[authMode];

  const msgColor = messageType === "success" ? "#16a34a" : messageType === "error" ? "#dc2626" : "#0369a1";

  return (
    <StudentShellClient title="AI 模型设置">
      <div style={{ maxWidth: 720, margin: "0 auto", padding: "24px" }}>
        <SectionCard title="文心一言 API 密钥">
          <p style={{ fontSize: "0.875rem", color: "#666", marginBottom: "16px" }}>
            选择 API 模式并输入对应密钥，即可在本系统中使用文心一言大模型进行智能分析。
            密钥将加密存储在服务器端，不会以明文形式保存或传输。
          </p>

          {loading ? (
            <p style={{ color: "#888" }}>加载中...</p>
          ) : (
            <>
              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", fontSize: "0.875rem", marginBottom: "8px", fontWeight: 500 }}>
                  API 模式
                </label>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    onClick={() => handleModeSwitch("qianfan")}
                    style={{
                      flex: 1, padding: "10px 16px", fontSize: "0.875rem", cursor: "pointer",
                      border: authMode === "qianfan" ? "2px solid #4f46e5" : "1px solid #d1d5db",
                      borderRadius: "8px", background: authMode === "qianfan" ? "#eef2ff" : "#fff",
                      color: authMode === "qianfan" ? "#4f46e5" : "#666", fontWeight: authMode === "qianfan" ? 600 : 400,
                    }}
                  >
                    新版千帆 V2
                  </button>
                  <button
                    onClick={() => handleModeSwitch("aistudio")}
                    style={{
                      flex: 1, padding: "10px 16px", fontSize: "0.875rem", cursor: "pointer",
                      border: authMode === "aistudio" ? "2px solid #4f46e5" : "1px solid #d1d5db",
                      borderRadius: "8px", background: authMode === "aistudio" ? "#eef2ff" : "#fff",
                      color: authMode === "aistudio" ? "#4f46e5" : "#666", fontWeight: authMode === "aistudio" ? 600 : 400,
                    }}
                  >
                    旧版 AI Studio
                  </button>
                </div>
              </div>

              <div style={{ marginBottom: "12px", padding: "10px", background: "#f8fafc", borderRadius: "6px", fontSize: "0.8125rem", color: "#555" }}>
                <strong>{currentModeInfo.title}</strong>
                <p style={{ margin: "4px 0" }}>{currentModeInfo.desc}</p>
                <p style={{ margin: "2px 0" }}>获取方式：<a href={currentModeInfo.link} target="_blank" rel="noopener noreferrer" style={{ color: "#4f46e5" }}>{currentModeInfo.linkText}</a></p>
                <p style={{ margin: "2px 0", color: "#888", fontFamily: "monospace" }}>{currentModeInfo.apiHint}</p>
              </div>

              {status?.configured && (
                <div style={{ marginBottom: "16px", padding: "10px", background: "#f0fdf4", borderRadius: "6px", fontSize: "0.8125rem" }}>
                  <strong style={{ color: "#16a34a" }}>当前已配置密钥：</strong>
                  <div style={{ marginTop: "4px", color: "#555" }}>
                    API Key: <code style={{ background: "#e2e8f0", padding: "1px 4px", borderRadius: "3px" }}>{status.api_key_masked || "***"}</code>
                    {status.auth_mode === "qianfan" && (
                      <>
                        {" "}&nbsp; Secret Key: <code style={{ background: "#e2e8f0", padding: "1px 4px", borderRadius: "3px" }}>{status.secret_key_masked || "***"}</code>
                      </>
                    )}
                    {" "}&nbsp; 模式: <code style={{ background: "#e2e8f0", padding: "1px 4px", borderRadius: "3px" }}>{status.auth_mode === "qianfan" ? "千帆 V2" : "AI Studio"}</code>
                  </div>
                </div>
              )}

              <div style={{ marginBottom: "12px" }}>
                <label htmlFor="api_key" style={{ display: "block", fontSize: "0.875rem", marginBottom: "4px", fontWeight: 500 }}>
                  API Key
                </label>
                <input
                  id="api_key"
                  type={showKey ? "text" : "password"}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={status?.configured ? "已配置，如需更换请输入新的 API Key" : "请输入 API Key"}
                  style={{ width: "100%", padding: "8px 12px", border: "1px solid #d1d5db", borderRadius: "6px", fontSize: "0.875rem" }}
                />
              </div>

              {authMode === "qianfan" && (
                <div style={{ marginBottom: "12px" }}>
                  <label htmlFor="secret_key" style={{ display: "block", fontSize: "0.875rem", marginBottom: "4px", fontWeight: 500 }}>
                    Secret Key
                  </label>
                  <input
                    id="secret_key"
                    type={showKey ? "text" : "password"}
                    value={secretKey}
                    onChange={(e) => setSecretKey(e.target.value)}
                    placeholder={status?.secret_key_masked ? "已配置，如需更换请输入新的 Secret Key" : "请输入 Secret Key"}
                    style={{ width: "100%", padding: "8px 12px", border: "1px solid #d1d5db", borderRadius: "6px", fontSize: "0.875rem" }}
                  />
                </div>
              )}

              <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  style={{ padding: "8px 20px", fontSize: "0.875rem", background: "#4f46e5", color: "#fff", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: 500 }}
                >
                  {saving ? "保存中..." : "保存密钥"}
                </button>
                {status?.configured && (
                  <button
                    onClick={handleTest}
                    disabled={testing}
                    style={{ padding: "8px 20px", fontSize: "0.875rem", background: "#0284c7", color: "#fff", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: 500 }}
                  >
                    {testing ? "验证中..." : "验证密钥"}
                  </button>
                )}
                {status?.configured && (
                  <button
                    onClick={handleDelete}
                    disabled={saving}
                    style={{ padding: "8px 20px", fontSize: "0.875rem", background: "#fee2e2", color: "#dc2626", border: "1px solid #fca5a5", borderRadius: "6px", cursor: "pointer" }}
                  >
                    删除密钥
                  </button>
                )}
                <label style={{ fontSize: "0.8125rem", color: "#666", cursor: "pointer", display: "flex", alignItems: "center", gap: "4px" }}>
                  <input type="checkbox" checked={showKey} onChange={(e) => setShowKey(e.target.checked)} />
                  显示密钥
                </label>
              </div>

              {message && (
                <div style={{ marginTop: "12px", padding: "10px", background: messageType === "success" ? "#f0fdf4" : messageType === "error" ? "#fef2f2" : "#f0f9ff", borderRadius: "6px", fontSize: "0.875rem", color: msgColor }}>
                  {message}
                </div>
              )}

              <div style={{ marginTop: "16px", padding: "12px", background: status?.configured ? "#f0fdf4" : "#f0f9ff", borderRadius: "6px", fontSize: "0.8125rem", color: status?.configured ? "#16a34a" : "#0369a1" }}>
                <strong>当前状态：</strong>
                {status?.configured ? (
                  <>
                    已配置 ({status.auth_mode === "qianfan" ? "千帆 V2" : "AI Studio"})
                    {status.model_name && ` — 模型: ${status.model_name}`}
                  </>
                ) : (
                  "未配置 — 将使用内置模拟数据"
                )}
              </div>
            </>
          )}
        </SectionCard>
      </div>
    </StudentShellClient>
  );
}
