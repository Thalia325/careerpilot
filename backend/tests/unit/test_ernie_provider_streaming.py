from types import SimpleNamespace

from app.integrations.llm.providers import ErnieLLMProvider


def test_extract_json_accepts_trailing_text():
    text = '{"skills":["Python"],"capability_scores":{"learning":88}}\n补充说明：以上为分析结果。'
    parsed = ErnieLLMProvider._extract_json(text)

    assert parsed["skills"] == ["Python"]
    assert parsed["capability_scores"]["learning"] == 88


def test_chat_ignores_reasoning_content():
    provider = ErnieLLMProvider(access_token="token")

    class FakeCompletions:
        @staticmethod
        def create(**kwargs):
            assert kwargs["stream"] is True
            assert kwargs["extra_body"]["web_search"]["enable"] is True
            assert kwargs["max_completion_tokens"] == 65536
            return [
                SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            delta=SimpleNamespace(reasoning_content="先分析一下", content=None)
                        )
                    ]
                ),
                SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            delta=SimpleNamespace(reasoning_content=None, content='{"ok":')
                        )
                    ]
                ),
                SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            delta=SimpleNamespace(reasoning_content=None, content='"yes"}')
                        )
                    ]
                ),
            ]

    provider.client = SimpleNamespace(
        chat=SimpleNamespace(completions=FakeCompletions())
    )

    result = provider._chat("system", "user")

    assert result == '{"ok":"yes"}'


def test_generate_report_falls_back_to_mock_on_timeout():
    provider = ErnieLLMProvider(access_token="token")

    async def fake_report(payload):
        return {"content": {"student_summary": {}}, "markdown_content": "# mock"}

    async def run():
        provider.mock.generate_report = fake_report
        provider._request_json = lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError("The read operation timed out"))
        result = await provider.generate_report({"student_name": "测试"})
        assert result["markdown_content"] == "# mock"

    import asyncio

    asyncio.run(run())
