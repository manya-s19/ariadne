# app.py
#
# PURPOSE: Live Ariadne dashboard - shows GPS spoofing being detected and mitigated
#          across three real UAE flight paths.
#
# LAYOUT:
#   Left sidebar  - map, flight path selector, run button, status panels
#   Right main    - narrative banner, position chart, residual chart, event log
#
# HOW TO RUN (from ariadne/ root):
#   python3 -m dashboard.app
#   Open http://127.0.0.1:8050

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go

from dashboard.real_data import FLIGHT_PATHS, run_flight_path

# ---------------------------------------------------------------------------
# APP INIT
# ---------------------------------------------------------------------------
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # for deployment
app.title = "Ariadne — Navigation Integrity Monitor"

# ---------------------------------------------------------------------------
# COLOUR SCHEME
# ---------------------------------------------------------------------------
C = {
    "bg":     "#0d1117",
    "panel":  "#161b22",
    "border": "#30363d",
    "text":   "#e6edf3",
    "green":  "#3fb950",
    "yellow": "#d29922",
    "orange": "#f0883e",
    "red":    "#f85149",
    "blue":   "#58a6ff",
    "purple": "#bc8cff",
    "grey":   "#8b949e",
    "teal":   "#39d0c4",
}

THREAT_COLOURS = {
    "LOW":      C["green"],
    "MEDIUM":   C["yellow"],
    "HIGH":     C["orange"],
    "CRITICAL": C["red"],
}

# Mahalanobis thresholds matching Kalman Filter's classifier
FLAG_THRESHOLD     = 3.0
ELIMINATE_THRESHOLD = 5.0

PATH_COLOURS = {
    "abu_dhabi_fujairah":   C["teal"],
    "dubai_ras_al_khaimah": C["purple"],
    "abu_dhabi_al_ain":     C["orange"],
}

CITIES = {
    "Abu Dhabi":      (24.4667, 54.3667),
    "Fujairah":       (25.1221, 56.3345),
    "Dubai":          (25.2532, 55.3657),
    "Ras Al Khaimah": (25.7953, 55.9432),
    "Al Ain":         (24.2075, 55.7447),
}

# ---------------------------------------------------------------------------
# HELPER COMPONENTS
# ---------------------------------------------------------------------------

def panel(children, extra_style=None):
    style = {
        "backgroundColor": C["panel"],
        "border":          f"1px solid {C['border']}",
        "borderRadius":    "8px",
        "padding":         "14px",
    }
    if extra_style:
        style.update(extra_style)
    return html.Div(children, style=style)


def small_label(text):
    return html.P(text, style={
        "color":         C["grey"],
        "fontSize":      "10px",
        "letterSpacing": "1.5px",
        "textTransform": "uppercase",
        "margin":        "0 0 8px 0",
    })


def sensor_badge(name, state):
    colour_map = {
        "IN_KF":      C["green"],
        "FLAGGED":    C["yellow"],
        "ELIMINATED": C["red"],
        "STANDBY":    C["grey"],
    }
    c = colour_map.get(state, C["grey"])
    return html.Div([
        html.Span(name, style={
            "fontWeight": "bold", "marginRight": "8px",
            "minWidth": "36px", "display": "inline-block",
            "fontSize": "12px",
        }),
        html.Span(state, style={
            "backgroundColor": c,
            "color":           "#0d1117",
            "padding":         "2px 8px",
            "borderRadius":    "3px",
            "fontSize":        "10px",
            "fontWeight":      "bold",
        }),
    ], style={"marginBottom": "8px", "display": "flex", "alignItems": "center"})


def empty_fig(height=None):
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor=C["panel"],
        plot_bgcolor=C["panel"],
        font_color=C["text"],
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
    )
    return fig


def build_map(selected=None):
    fig = go.Figure()
    for key, cfg in FLIGHT_PATHS.items():
        is_sel  = (selected is None or key == selected)
        opacity = 1.0 if is_sel else 0.2
        colour  = PATH_COLOURS[key]
        fig.add_trace(go.Scattergeo(
            lat=[cfg["start_lat"], cfg["end_lat"]],
            lon=[cfg["start_lon"], cfg["end_lon"]],
            mode="lines+markers",
            line=dict(width=3 if is_sel else 1.5, color=colour),
            marker=dict(size=7, color=colour),
            opacity=opacity,
            name=cfg["label"],
            hovertemplate=(
                f"<b>{cfg['label']}</b><br>"
                f"Terrain: {cfg['terrain']}<br>"
                f"Attack: {cfg['spoof_type']}<extra></extra>"
            ),
        ))
    fig.add_trace(go.Scattergeo(
        lat=[v[0] for v in CITIES.values()],
        lon=[v[1] for v in CITIES.values()],
        mode="markers+text",
        marker=dict(size=6, color=C["text"]),
        text=list(CITIES.keys()),
        textposition="top right",
        textfont=dict(color=C["text"], size=10),
        hoverinfo="text",
        showlegend=False,
    ))
    fig.update_layout(
        geo=dict(
            scope="asia",
            showland=True,      landcolor="#1c2333",
            showocean=True,     oceancolor="#0d1117",
            showlakes=False,
            showcountries=True, countrycolor=C["border"],
            showcoastlines=True, coastlinecolor=C["border"],
            showrivers=False,
            bgcolor=C["bg"],
            center=dict(lat=24.8, lon=55.3),
            projection_scale=12,
        ),
        paper_bgcolor=C["bg"],
        font_color=C["text"],
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(
            orientation="v", x=0.01, y=0.99,
            bgcolor="rgba(22,27,34,0.85)",
            bordercolor=C["border"], borderwidth=1,
            font=dict(size=10, color=C["text"]),
        ),
        height=250,
    )
    return fig


# ---------------------------------------------------------------------------
# LAYOUT
# ---------------------------------------------------------------------------

app.layout = html.Div(style={
    "backgroundColor": C["bg"],
    "color":           C["text"],
    "fontFamily":      "monospace",
    "padding":         "16px",
    "minHeight":       "100vh",
}, children=[

    # ── HEADER ───────────────────────────────────────────────────────────────
    html.Div(style={"marginBottom": "14px", "display": "flex", "alignItems": "baseline",
                    "gap": "12px"}, children=[
        html.H1("ARIADNE", style={
            "color": C["blue"], "margin": "0",
            "fontSize": "24px", "letterSpacing": "4px",
        }),
        html.Span("Terrain-Authenticated GPS Spoofing Detection",
                  style={"color": C["grey"], "fontSize": "11px", "letterSpacing": "1px"}),
    ]),

    # ── MAIN BODY ────────────────────────────────────────────────────────────
    html.Div(style={"display": "flex", "gap": "14px", "alignItems": "flex-start"}, children=[

        # ── LEFT SIDEBAR ─────────────────────────────────────────────────────
        html.Div(style={"width": "270px", "flexShrink": "0"}, children=[

            # Map
            panel([
                small_label("UAE Test Routes"),
                dcc.Graph(
                    id="map-figure",
                    figure=build_map(),
                    config={"displayModeBar": False},
                    style={"height": "250px"},
                ),
            ], extra_style={"marginBottom": "10px", "padding": "10px"}),

            # Flight path selector + run button
            panel([
                small_label("Select Test Case"),
                dcc.RadioItems(
                    id="flightpath-selector",
                    options=[
                        {
                            "label": html.Div([
                                html.Div(cfg["label"], style={
                                    "fontWeight": "bold", "fontSize": "12px",
                                    "color": PATH_COLOURS[key],
                                }),
                                html.Div(
                                    f"{cfg['terrain']} · {cfg['spoof_type'].upper()}",
                                    style={"color": C["grey"], "fontSize": "10px"},
                                ),
                            ], style={"padding": "3px 0"}),
                            "value": key,
                        }
                        for key, cfg in FLIGHT_PATHS.items()
                    ],
                    value="abu_dhabi_fujairah",
                    inputStyle={"marginRight": "8px", "accentColor": C["blue"]},
                    style={"marginBottom": "10px"},
                ),
                html.Button("▶  RUN SIMULATION", id="run-btn", n_clicks=0, style={
                    "width":           "100%",
                    "backgroundColor": C["blue"],
                    "color":           C["bg"],
                    "border":          "none",
                    "padding":         "9px",
                    "cursor":          "pointer",
                    "borderRadius":    "4px",
                    "fontFamily":      "monospace",
                    "fontWeight":      "bold",
                    "letterSpacing":   "1px",
                    "fontSize":        "12px",
                }),
            ], extra_style={"marginBottom": "10px"}),

            # Threat level + dead reckoning
            panel([
                small_label("Threat Level"),
                html.Div(id="threat-panel", style={"marginBottom": "12px"}),
                html.Hr(style={"borderColor": C["border"], "margin": "6px 0"}),
                small_label("Dead Reckoning"),
                html.Div(id="dead-reckoning-panel"),
            ], extra_style={"marginBottom": "10px"}),

            # Sensor status
            panel([
                small_label("Sensor Status"),
                html.Div(id="sensor-status-panel"),
            ]),
        ]),

        # ── RIGHT: narrative + charts + log ──────────────────────────────────
        html.Div(style={"flex": "1", "minWidth": "0"}, children=[

            # ── NARRATIVE BANNER ─────────────────────────────────────────────
            # Explains in plain language what Ariadne is doing right now.
            # Updates live as the simulation progresses.
            html.Div(id="narrative-banner", style={"marginBottom": "10px"}),

            # ── POSITION CHART ───────────────────────────────────────────────
            # The key visual: all sensors plotted together.
            # When GPS is spoofed you see it peel away from the true position.
            # IRS, TRN, and Kalman stay clustered near the truth - that cluster
            # IS Ariadne working. GPS turns red when flagged/eliminated.
            panel([
                html.Div(style={"display": "flex", "justifyContent": "space-between",
                                "alignItems": "flex-start", "marginBottom": "4px"}, children=[
                    small_label("Position Over Time — all sensors"),
                    html.Div(id="chart-annotation", style={
                        "fontSize": "10px", "color": C["grey"], "textAlign": "right",
                        "maxWidth": "320px", "lineHeight": "1.5",
                    }),
                ]),
                dcc.Graph(id="position-chart", style={"height": "280px"},
                          config={"displayModeBar": False}),
            ], extra_style={"marginBottom": "10px"}),

            # ── RESIDUAL CHART ────────────────────────────────────────────────
            # Shows the Mahalanobis distance over time — the detection mechanism.
            # Crossing 3σ → GPS FLAGGED. Crossing 5σ → GPS ELIMINATED.
            panel([
                small_label("Mahalanobis Distance — how statistically abnormal is GPS?"),
                dcc.Graph(id="residual-chart", style={"height": "180px"},
                          config={"displayModeBar": False}),
            ], extra_style={"marginBottom": "10px"}),

            # ── EVENT LOG ─────────────────────────────────────────────────────
            panel([
                small_label("Event Log — timestamped detection history"),
                html.Div(id="event-log", style={
                    "height":    "120px",
                    "overflowY": "scroll",
                    "fontSize":  "11px",
                    "lineHeight": "1.6",
                }),
            ]),
        ]),
    ]),

    # ── STORES + TICK ─────────────────────────────────────────────────────────
    dcc.Store(id="simulation-store", data=[]),
    dcc.Store(id="history-store",    data=[]),
    dcc.Store(id="t-store",          data=0),
    dcc.Interval(id="tick", interval=700, n_intervals=0),
])


# ---------------------------------------------------------------------------
# CALLBACK 1: Map highlight
# ---------------------------------------------------------------------------

@app.callback(
    Output("map-figure", "figure"),
    Input("flightpath-selector", "value"),
)
def update_map(path_key):
    return build_map(selected=path_key)


# ---------------------------------------------------------------------------
# CALLBACK 2: RUN button — precompute simulation
# ---------------------------------------------------------------------------

@app.callback(
    Output("simulation-store", "data"),
    Output("history-store",    "data"),
    Output("t-store",          "data"),
    Input("run-btn",             "n_clicks"),
    State("flightpath-selector", "value"),
    prevent_initial_call=True,
)
def run_simulation(n_clicks, path_key):
    frames = run_flight_path(path_key, seconds=60)
    return frames, [], 0


# ---------------------------------------------------------------------------
# CALLBACK 3: Tick
# ---------------------------------------------------------------------------

@app.callback(
    Output("history-store", "data", allow_duplicate=True),
    Output("t-store",       "data", allow_duplicate=True),
    Input("tick", "n_intervals"),
    State("simulation-store", "data"),
    State("history-store",    "data"),
    State("t-store",          "data"),
    prevent_initial_call=True,
)
def tick(_, simulation, history, t):
    if not simulation or t >= len(simulation):
        return history, t
    history.append(simulation[t])
    if len(history) > 100:
        history = history[-100:]
    return history, t + 1


# ---------------------------------------------------------------------------
# CALLBACK 4: Update all visuals
# ---------------------------------------------------------------------------

@app.callback(
    Output("position-chart",       "figure"),
    Output("residual-chart",       "figure"),
    Output("threat-panel",         "children"),
    Output("sensor-status-panel",  "children"),
    Output("dead-reckoning-panel", "children"),
    Output("event-log",            "children"),
    Output("narrative-banner",     "children"),
    Output("chart-annotation",     "children"),
    Input("history-store", "data"),
    prevent_initial_call=True,
)
def update_visuals(history):
    if not history:
        return empty_fig(), empty_fig(), "—", "—", "—", [], "", ""

    latest    = history[-1]
    ts        = [f["t"] for f in history]
    gps_state = latest.get("gps_state", "IN_KF")
    trn_state = latest.get("trn_state", "STANDBY")
    threat    = latest["threat_level"]
    dr_active = latest["dead_reckoning_active"]
    narrative = latest.get("narrative", {})
    spoof_type = latest.get("spoof_type", "")

    # ── POSITION CHART ────────────────────────────────────────────────────────
    # GPS line colour: blue when trusted, red when flagged/eliminated.
    # The visual divergence of the GPS line IS the spoofing attack made visible.
    gps_colour = C["blue"] if latest["gps_trusted"] else C["red"]

    pos = go.Figure()
    pos.add_trace(go.Scatter(
        x=ts, y=[f["true_position"] for f in history],
        name="True Position",
        line=dict(color=C["text"], dash="dot", width=3),
        mode="lines",
    ))
    pos.add_trace(go.Scatter(
        x=ts, y=[f["gps_position"] for f in history],
        name="GPS (spoofed → red)",
        line=dict(color=gps_colour, width=2.5),
        mode="lines",
    ))
    pos.add_trace(go.Scatter(
        x=ts, y=[f["irs_position"] for f in history],
        name="IRS (inertial)",
        line=dict(color=C["purple"], width=1.5),
        mode="lines",
    ))
    pos.add_trace(go.Scatter(
        x=ts, y=[f["trn_position"] for f in history],
        name="TRN (terrain)",
        line=dict(color=C["green"], width=1.5),
        mode="lines",
    ))
    pos.add_trace(go.Scatter(
        x=ts, y=[f["kalman_estimate"] for f in history],
        name="Kalman estimate",
        line=dict(color=C["yellow"], width=3),
        mode="lines",
    ))
    pos.add_trace(go.Scatter(
        x=ts, y=[f["naive_position"] for f in history],
        name="Without Ariadne (blind GPS)",
        line=dict(color=C["red"], width=1.5, dash="dot"),
        opacity=0.4,
        mode="lines",
    ))

    # Adding a vertical annotation line the moment GPS gets flagged
    for i, f in enumerate(history):
        if f.get("gps_state") == "FLAGGED" and (i == 0 or history[i-1].get("gps_state") == "IN_KF"):
            pos.add_vline(
                x=f["t"],
                line_dash="dash", line_color=C["yellow"], line_width=1,
                annotation_text="GPS FLAGGED",
                annotation_font_color=C["yellow"],
                annotation_font_size=10,
            )
        if f.get("gps_state") == "ELIMINATED" and (i == 0 or history[i-1].get("gps_state") != "ELIMINATED"):
            pos.add_vline(
                x=f["t"],
                line_dash="dash", line_color=C["red"], line_width=1,
                annotation_text="GPS ELIMINATED",
                annotation_font_color=C["red"],
                annotation_font_size=10,
            )


    # gap annotation
    if len(history) >= 60:
        naive_error = abs(history[-1]["naive_position"] - history[-1]["true_position"])
        ariadne_error = abs(history[-1]["kalman_estimate"] - history[-1]["true_position"])
        pos.add_annotation(
            x=52, y=history[-1]["naive_position"],
            text=f"Unprotected: {naive_error:.0f}m off course",
            font=dict(color=C["red"], size=10),
            showarrow=True, arrowhead = 2, arrowcolor=C["red"],
            ax=0, ay=-35,
            xanchor="right",
        )
        pos.add_annotation(
            x=52, y=history[-1]["kalman_estimate"],
            text=f"Ariadne: {ariadne_error:.0f}m error",
            font=dict(color=C["green"], size=10),
            showarrow=True, arrowhead=2, arrowcolor=C["green"],
            ax=0, ay=-35,
            xanchor="right",
        )

    pos.update_layout(
        paper_bgcolor=C["panel"], plot_bgcolor=C["bg"],
        font=dict(color=C["text"], family="monospace"),
        margin=dict(l=55, r=10, t=10, b=50),
        legend=dict(orientation="h", y=-0.22, font=dict(size=10)),
        xaxis=dict(title="Timestep", color=C["grey"], gridcolor=C["border"]),
        yaxis=dict(title="Position (m)", color=C["grey"], gridcolor=C["border"]),
        height=280,
    )

    # ── RESIDUAL CHART ────────────────────────────────────────────────────────
    res = go.Figure()
    res.add_trace(go.Scatter(
        x=ts, y=[f["residual"] for f in history],
        name="Mahalanobis distance",
        line=dict(color=C["orange"], width=2),
        mode="lines", fill="tozeroy",
        fillcolor="rgba(240,136,62,0.10)",
    ))
    res.add_hline(
        y=FLAG_THRESHOLD,
        line_dash="dash", line_color=C["yellow"],
        annotation_text="3σ — Flag GPS",
        annotation_font_color=C["yellow"], annotation_font_size=10,
        annotation_position="right",
    )
    res.add_hline(
        y=ELIMINATE_THRESHOLD,
        line_dash="dash", line_color=C["red"],
        annotation_text="5σ — Eliminate GPS",
        annotation_font_color=C["red"], annotation_font_size=10,
        annotation_position="right",
    )
    res.update_layout(
        paper_bgcolor=C["panel"], plot_bgcolor=C["bg"],
        font=dict(color=C["text"], family="monospace"),
        margin=dict(l=55, r=120, t=10, b=50),
        xaxis=dict(title="Timestep", color=C["grey"], gridcolor=C["border"]),
        yaxis=dict(title="σ (sigma)", color=C["grey"], gridcolor=C["border"]),
        height=180,
    )

    # ── THREAT PANEL ──────────────────────────────────────────────────────────
    threat_content = html.Div([
        html.Div(threat, style={
            "color":      THREAT_COLOURS[threat],
            "fontSize":   "26px",
            "fontWeight": "bold",
        }),
        html.Div(f"t = {latest['t']} / 59",
                 style={"color": C["grey"], "fontSize": "10px", "marginTop": "4px"}),
    ])

    # ── SENSOR STATUS ─────────────────────────────────────────────────────────
    sensor_content = html.Div([
        sensor_badge("GPS", gps_state),
        sensor_badge("IRS", "IN_KF"),
        sensor_badge("TRN", trn_state),
        html.Div(f"Anomaly score: {latest['residual']:.2f}σ",
                 style={"color": C["grey"], "fontSize": "10px", "marginTop": "6px"}),
    ])

    # ── DEAD RECKONING ────────────────────────────────────────────────────────
    dr_content = html.Div([
        html.Span(
            "ACTIVE" if dr_active else "STANDBY",
            style={"color": C["red"] if dr_active else C["green"], "fontWeight": "bold"},
        ),
        html.Div(
            "IRS only — no external fix" if dr_active else "External sensors nominal",
            style={"color": C["grey"], "fontSize": "10px", "marginTop": "4px"},
        ),
    ])

    # ── EVENT LOG ─────────────────────────────────────────────────────────────
    entries  = []
    prev_state = "IN_KF"
    for f in history:
        s = f.get("gps_state", "IN_KF")
        if s != prev_state:
            if s == "FLAGGED":
                msg, col = "GPS FLAGGED — Mahalanobis > 3σ. Monitoring.", C["yellow"]
            elif s == "ELIMINATED":
                msg, col = "GPS ELIMINATED — Mahalanobis > 5σ. Excluded from navigation.", C["red"]
            elif prev_state != "IN_KF":
                msg, col = "GPS RECOVERED — reinstated to Kalman filter.", C["green"]
            else:
                msg, col = None, None
            if msg:
                entries.append(html.Div(
                    f"[t={f['t']:>3}]  {msg}",
                    style={"color": col, "padding": "2px 0",
                           "borderBottom": f"1px solid {C['border']}"},
                ))
        prev_state = s
        if f["dead_reckoning_active"]:
            entries.append(html.Div(
                f"[t={f['t']:>3}]  DEAD RECKONING — IRS-only navigation active.",
                style={"color": C["orange"], "padding": "2px 0",
                       "borderBottom": f"1px solid {C['border']}"},
            ))

    log = list(reversed(entries)) if entries else [
        html.Span("No events yet. Waiting for anomaly...",
                  style={"color": C["grey"]}),
    ]

    # ── NARRATIVE BANNER ──────────────────────────────────────────────────────
    # Shows a different message depending on current system state.
    # This is how the dashboard explains what Ariadne is doing to a viewer.
    if dr_active:
        banner_colour  = C["red"]
        banner_title   = "⚠  DEAD RECKONING ACTIVE"
        banner_body    = (
            "Both GPS and IRS are compromised. Ariadne has activated dead reckoning — "
            "the aircraft navigates using its last known good position and velocity. "
            "This is the fallback of last resort."
        )
    elif gps_state == "ELIMINATED":
        banner_colour  = C["red"]
        banner_title   = "✗  GPS ELIMINATED — TRN NAVIGATING"
        banner_body    = (
            f"GPS spoofing confirmed ({latest['residual']:.1f}σ > 5σ threshold). "
            "GPS has been excluded from the Kalman filter. "
            "Ariadne is now navigating using Terrain-Relative Navigation (TRN) — "
            "cross-referencing radar returns against the preloaded elevation map."
        )
    elif gps_state == "FLAGGED":
        banner_colour  = C["yellow"]
        banner_title   = "⚡  GPS FLAGGED — ANOMALY DETECTED"
        banner_body    = (
            f"GPS readings are statistically suspicious ({latest['residual']:.1f}σ > 3σ). "
            "The Kalman filter is tracking the divergence. "
            "If the anomaly persists above 5σ, GPS will be eliminated and TRN takes over."
        )
    elif latest["t"] < 5:
        banner_colour  = C["blue"]
        banner_title   = "●  SIMULATION RUNNING"
        banner_body    = narrative.get("route", "") + "  |  " + narrative.get("attack", "")
    else:
        banner_colour  = C["green"]
        banner_title   = "✓  ALL SENSORS NOMINAL"
        banner_body    = (
            "GPS, IRS, and TRN are all in agreement. "
            "The Kalman filter is fusing all three to produce the best position estimate. "
            "Mahalanobis distance is within normal bounds."
        )

    banner = panel([
        html.Div(style={"display": "flex", "gap": "10px", "alignItems": "flex-start"}, children=[
            html.Div(style={
                "width":           "4px",
                "borderRadius":    "2px",
                "backgroundColor": banner_colour,
                "flexShrink":      "0",
                "alignSelf":       "stretch",
            }),
            html.Div([
                html.Div(banner_title, style={
                    "color":      banner_colour,
                    "fontWeight": "bold",
                    "fontSize":   "12px",
                    "marginBottom": "4px",
                }),
                html.Div(banner_body, style={
                    "color":      C["text"],
                    "fontSize":   "11px",
                    "lineHeight": "1.6",
                }),
            ]),
        ]),
    ], extra_style={"marginBottom": "10px"})

    # ── CHART ANNOTATION (top-right of position chart) ─────────────────────────
    #  reminder of what to look for in the chart.
    spoof_hints = {
        "gradual":  "Watch the GPS line drift away slowly from the cluster →",
        "sudden":   "Watch for GPS to snap to a false position all at once →",
        "combined": "Both GPS and IRS diverge — Kalman holds position alone →",
        "none":     "All sensors tracking together — clean flight.",
    }
    chart_note = spoof_hints.get(spoof_type, "")

    return (pos, res, threat_content, sensor_content,
            dr_content, log, banner, chart_note)


# ---------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
