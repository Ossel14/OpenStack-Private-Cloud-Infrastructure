
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

SLA_FILE = '/opt/stack/openstack-monitoring/sla.json'
ALERTS_FILE = '/opt/stack/openstack-monitoring/alerts.json'

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        with open(SLA_FILE) as f:
            data = json.load(f)

        # Read alerts
        alerts = []
        try:
            with open(ALERTS_FILE) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        alerts.append(json.loads(line))
        except:
            alerts = []

        # Get data
        availability = data['report']['current_availability']
        status = data['report']['objective_met']
        last_check = data['report']['last_check']
        total = data['report']['total_vms']
        active = data['report']['active_vms']
        history = data.get('history', [])
        color = "#00ff64" if status == "SUCCESS" else "#ff4444"
        avail_float = float(availability.replace('%',''))

        # Build history rows
        history_rows = ""
        for h in reversed(history[-10:]):
            c = "#00ff64" if h['status'] == "SUCCESS" else "#ff4444"
            history_rows += f"""
            <tr>
                <td>{h['timestamp']}</td>
                <td style="color:{c}">{h['availability']:.2f}%</td>
                <td style="color:{c}">{h['status']}</td>
            </tr>"""

        # Build alerts rows
        alert_rows = ""
        for a in reversed(alerts[-5:]):
            c = "#ff4444" if a['alert_type'] == "SLA_VIOLATION" else "#00ff64"
            alert_rows += f"""
            <tr>
                <td>{a['timestamp']}</td>
                <td style="color:{c}">{a['alert_type']}</td>
                <td>{a['message']}</td>
            </tr>"""

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OpenStack SLA Dashboard</title>
            <meta http-equiv="refresh" content="30">
            <style>
                * {{ margin:0; padding:0; box-sizing:border-box; }}
                body {{ font-family: 'Segoe UI', sans-serif; 
                        background: #0f0f1a; color: white; padding: 30px; }}
                h1 {{ font-size: 1.8em; margin-bottom: 5px; }}
                .subtitle {{ color: #aaa; font-size: 14px; margin-bottom: 30px; }}
                .grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; 
                         gap: 20px; margin-bottom: 25px; }}
                .card {{ background: rgba(255,255,255,0.05); border-radius: 12px;
                         padding: 25px; border: 1px solid rgba(255,255,255,0.1); }}
                .card.wide {{ grid-column: span 2; }}
                .card.full {{ grid-column: span 4; }}
                .metric {{ text-align: center; }}
                .metric .number {{ font-size: 2.5em; font-weight: bold; 
                                   color: {color}; }}
                .metric .label {{ color: #aaa; font-size: 13px; margin-top: 8px; }}
                .status-badge {{ display: inline-block; padding: 8px 20px;
                                 border-radius: 50px; font-weight: bold;
                                 background: {'rgba(0,255,100,0.1)' if status == 'SUCCESS' else 'rgba(255,68,68,0.1)'};
                                 border: 1px solid {color}; color: {color}; }}
                .progress-bar {{ background: #333; border-radius: 10px; 
                                 height: 25px; overflow: hidden; margin-top: 15px; }}
                .progress-fill {{ background: {color}; 
                                  width: {min(avail_float, 100)}%;
                                  height: 100%; border-radius: 10px;
                                  transition: width 0.5s; }}
                table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
                th {{ color: #aaa; padding: 10px; text-align: left; 
                      border-bottom: 1px solid rgba(255,255,255,0.1); }}
                td {{ padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
                tr:hover {{ background: rgba(255,255,255,0.03); }}
                .dot {{ width: 10px; height: 10px; background: {color};
                        border-radius: 50%; display: inline-block;
                        animation: pulse 1.5s infinite; margin-right: 8px; }}
                @keyframes pulse {{
                    0%, 100% {{ opacity: 1; }}
                    50% {{ opacity: 0.3; }}
                }}
                .header {{ display: flex; justify-content: space-between; 
                           align-items: center; margin-bottom: 30px; }}
                .live {{ color: #aaa; font-size: 13px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div>
                    <h1>☁️ OpenStack SLA Dashboard</h1>
                    <div class="subtitle">
                        Prof. C. El Amrani — Cloud & Edge Computing | 
                        Auto-refresh every 30s
                    </div>
                </div>
                <div class="live">
                    <span class="dot"></span>
                    Last check: {last_check}
                </div>
            </div>

            <div class="grid">
                <!-- Availability -->
                <div class="card metric">
                    <div class="number">{avail_float:.1f}%</div>
                    <div class="label">Current Availability</div>
                </div>

                <!-- Status -->
                <div class="card metric">
                    <div style="margin-top:10px">
                        <span class="status-badge">
                            {'✅ SLA RESPECTED' if status == 'SUCCESS' else '❌ SLA VIOLATED'}
                        </span>
                    </div>
                    <div class="label" style="margin-top:15px">SLA Status</div>
                </div>

                <!-- Total VMs -->
                <div class="card metric">
                    <div class="number" style="color:#e94560">{total}</div>
                    <div class="label">Total VMs</div>
                </div>

                <!-- Active VMs -->
                <div class="card metric">
                    <div class="number" style="color:#00ff64">{active}</div>
                    <div class="label">Active VMs</div>
                </div>

                <!-- Progress Bar -->
                <div class="card wide">
                    <h3 style="margin-bottom:10px">Availability vs Target (99.5%)</h3>
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; 
                                margin-top:8px; color:#aaa; font-size:12px;">
                        <span>0%</span>
                        <span style="color:{color}">Current: {avail_float:.2f}%</span>
                        <span>Target: 99.5%</span>
                        <span>100%</span>
                    </div>
                </div>

                <!-- SLA Info -->
                <div class="card wide">
                    <h3 style="margin-bottom:15px">SLA Contract</h3>
                    <table>
                        <tr>
                            <td style="color:#aaa">Service</td>
                            <td>{data.get('service_name', 'OpenStack Monitor')}</td>
                        </tr>
                        <tr>
                            <td style="color:#aaa">Target</td>
                            <td>{data['target_availability_percentage']}%</td>
                        </tr>
                        <tr>
                            <td style="color:#aaa">Period</td>
                            <td>{data.get('evaluation_period', 'Daily')}</td>
                        </tr>
                        <tr>
                            <td style="color:#aaa">Status</td>
                            <td>{data.get('status', 'Operational')}</td>
                        </tr>
                    </table>
                </div>

                <!-- History -->
                <div class="card full">
                    <h3 style="margin-bottom:15px">📊 Recent History (Last 10 checks)</h3>
                    <table>
                        <tr>
                            <th>Timestamp</th>
                            <th>Availability</th>
                            <th>Status</th>
                        </tr>
                        {history_rows}
                    </table>
                </div>

                <!-- Alerts -->
                <div class="card full">
                    <h3 style="margin-bottom:15px">🚨 Recent Alerts (Last 5)</h3>
                    <table>
                        <tr>
                            <th>Timestamp</th>
                            <th>Type</th>
                            <th>Message</th>
                        </tr>
                        {alert_rows}
                    </table>
                </div>
            </div>
        </body>
        </html>
        """

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        pass

print("Dashboard running at http://192.168.56.102:8080")
HTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
