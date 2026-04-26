import asyncio
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, DataTable, RichLog, Static
from textual.binding import Binding
from textual.reactive import reactive
from bridge import get_state

class MHarnessApp(App):
    CSS = """
    Screen { background: #080810; }
    .main-grid { grid-size: 2; grid-columns: 2fr 3fr; grid-rows: 1fr; height: 100%; }
    .left-col { width: 100%; height: 100%; }
    .right-col { width: 100%; height: 100%; }
    DataTable { border: solid rgb(30,30,50); background: #0c0c18; }
    RichLog { border: solid rgb(30,30,50); background: #0a0a14; }
    Static { border: solid rgb(30,30,50); background: #0a0a14; color: #6b6b7b; }
    .status-bar { height: auto; padding: 1 2; background: #0f0f20; color: #00ff88; }
    .title { text-style: bold; color: #00ff88; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("p", "pause", "Pause", show=True),
        Binding("r", "resume", "Resume", show=True),
        Binding("k", "kill", "Panic", show=True),
    ]

    conn_status = reactive("🔴 OFFLINE")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("MHARNESS // SWARM CONTROL", classes="title")
        with Horizontal(classes="main-grid"):
            with Vertical(classes="left-col"):
                yield DataTable(id="agents_table")
            with Vertical(classes="right-col"):
                yield RichLog(id="memory_log", highlight=True, max_lines=1000)
                yield Static(id="metrics")
        yield Static(self.conn_status, id="status_bar", classes="status-bar")
        yield Footer()

    def on_mount(self):
        self.title = "MHarness TUI"
        table = self.query_one("#agents_table", DataTable)
        table.add_columns("ID", "STATUS", "MODEL", "COST", "LAT")
        self.set_interval(2.0, self.refresh_data)

    async def refresh_data(self):
        data = get_state()
        is_mock = data.get("_source") == "mock" or data.get("swarm_state") == "mock"
        self.conn_status = "🟢 LIVE" if not is_mock else "🟡 DEMO (core offline)"
        self.query_one("#status_bar", Static).update(self.conn_status)

        table = self.query_one("#agents_table", DataTable)
        table.clear()
        for a in data.get("agents", []):
            table.add_row(
                a["id"],
                a["status"],
                a.get("model", "?"),
                f'{a.get("last_cost", 0):.4f}',
                f'{a.get("last_latency_ms", 0)}ms',
            )
        self.query_one("#metrics", Static).update(
            f"Total Cost: ${data.get('total_cost_session', 0):.4f}  |  "
            f"Queue: {data.get('queue_depth', 0)}  |  "
            f"State: {data.get('swarm_state', '?')}"
        )
        log = self.query_one("#memory_log", RichLog)
        mem = data.get("memory_snippet", "")
        if mem and (not hasattr(self, "_last_mem") or self._last_mem != mem):
            log.write(f'[{asyncio.get_event_loop().time():.0f}] {mem}')
            self._last_mem = mem

    def action_pause(self):
        self.query_one("#memory_log", RichLog).write(
            "[PAUSE] Signal emitted (stub)"
        )

    def action_resume(self):
        self.query_one("#memory_log", RichLog).write(
            "[RESUME] Signal emitted (stub)"
        )

    def action_kill(self):
        self.query_one("#memory_log", RichLog).write(
            "[PANIC] Kill signal emitted!"
        )

if __name__ == "__main__":
    MHarnessApp().run()