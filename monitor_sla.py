import openstack
import json
import datetime
import os

# Connect with hardcoded credentials (works in cron)
conn = openstack.connect(
    auth_url='http://192.168.56.102/identity/v3',
    project_name='demo',
    username='demo',
    password='admin',
    user_domain_name='Default',
    project_domain_name='Default'
)

SLA_FILE = '/opt/stack/openstack-monitoring/sla.json'
ALERTS_FILE = '/opt/stack/openstack-monitoring/alerts.json'

def send_alert(availability, status):
    """Save alert to alerts.json file"""
    alert = {
        "timestamp": str(datetime.datetime.now()),
        "alert_type": "SLA_VIOLATION" if status == "FAILED" else "SLA_OK",
        "availability": availability,
        "message": f"ALERT: Availability dropped to {availability}%"
                   if status == "FAILED"
                   else f"OK: Availability is {availability}%"
    }
    with open(ALERTS_FILE, 'a') as f:
        json.dump(alert, f)
        f.write('\n')
    print(alert['message'])

def check_availability():
    # 1. Get all VMs from Nova API
    servers = list(conn.compute.servers())
    total_vms = len(servers)
    active_vms = sum(1 for s in servers if s.status == 'ACTIVE')
    availability_rate = (active_vms / total_vms) * 100 if total_vms > 0 else 0

    # 2. Load SLA file
    with open(SLA_FILE, 'r') as f:
        sla_data = json.load(f)

    # 3. Check if SLA is met
    status_msg = "SUCCESS" if availability_rate >= sla_data['target_availability_percentage'] else "FAILED"

    # 4. Add to history (keeps last 100 entries)
    if 'history' not in sla_data:
        sla_data['history'] = []

    sla_data['history'].append({
        "timestamp": str(datetime.datetime.now()),
        "availability": availability_rate,
        "status": status_msg
    })

    # Keep only last 100 entries
    sla_data['history'] = sla_data['history'][-100:]

    # 5. Update current report
    sla_data['report'] = {
        "last_check": str(datetime.datetime.now()),
        "total_vms": total_vms,
        "active_vms": active_vms,
        "current_availability": f"{availability_rate}%",
        "objective_met": status_msg
    }

    # 6. Save updated SLA file
    with open(SLA_FILE, 'w') as f:
        json.dump(sla_data, f, indent=4)

    # 7. Send alert
    send_alert(availability_rate, status_msg)

    print(f"Monitoring complete. Availability: {availability_rate}%. Objective: {status_msg}")

if __name__ == "__main__":
    check_availability()
    