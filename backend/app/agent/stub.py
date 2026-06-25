"""Echo stub agent — used to TEST the whitelist routing. Replace with a real agent."""


class StubAgent:
    name = "echo-stub"

    async def reply(self, ctx: dict) -> str:
        body = (ctx.get("body") or "").strip()
        if body:
            return f'[AUTO] Anda menulis: "{body[:200]}"'
        canned = (
            "Halo! Ini balasan otomatis dari Satu Cakrawala.",
            "Pesan Anda kami terima, tim kami akan segera menindaklanjuti.",
            "Terima kasih sudah menghubungi Satu Cakrawala.",
        )
        seed = len(ctx.get("body") or "") + len(ctx.get("phone") or "")
        return f"[AUTO] {canned[seed % len(canned)]}"


stub_agent = StubAgent()
