# Aegis Arena - Decentralized Stadium Agent Mesh Backend
# FastAPI App, WebSockets, and Asynchronous Python Agents

import asyncio
import json
import os
import random
import time
from typing import Dict, List, Optional
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Initialize environment config
load_dotenv()

app = FastAPI(title="Aegis Arena Stadium Agent Mesh Backend")

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 1. WEBSOCKET CONNECTION GATEWAY
# ==========================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def class_connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def class_disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        payload = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                # Handle stale connections
                pass

manager = ConnectionManager()

# ==========================================
# 2. SHARED EVENT BUS (PYTHON ASYNC PATTERN)
# ==========================================
class PythonEventBus:
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_name: str, callback):
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)

    async def publish(self, event_name: str, data: dict):
        # Broadcast event to frontend Shared Event Bus ticker HUD
        hud_packet = {
            "type": "EVENT_BUS_LOG",
            "event": event_name,
            "data": data
        }
        await manager.broadcast(hud_packet)

        # Notify active subscribers in Python
        if event_name in self.subscribers:
            for callback in self.subscribers[event_name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    print(f"Error in EventBus subscriber callback: {e}")

# Instantiate global event bus
event_bus = PythonEventBus()

# ==========================================
# 3. GLOBAL TELEMETRY STATE
# ==========================================
class TelemetryState:
    def __init__(self):
        self.active_incident = None # None, 'surge', 'weather', 'threat', 'medical'
        self.autopilot = False
        self.attendance = 74820
        self.peak_density = 93.5
        self.flow_rate = 1240
        
        self.sectors = {
            "A": {"name": "Stand A (North)", "occupancy": 18450, "capacity": 20000, "state": "safe"},
            "B": {"name": "Stand B (East)", "occupancy": 19120, "capacity": 20000, "state": "safe"},
            "C": {"name": "Stand C (South)", "occupancy": 17850, "capacity": 20000, "state": "safe"},
            "D": {"name": "Stand D (West)", "occupancy": 19400, "capacity": 20000, "state": "safe"}
        }
        
        self.gates = {
            1: {"name": "Gate 1 (NW)", "state": "open", "rate": 120, "max": 250},
            2: {"name": "Gate 2 (N)", "state": "open", "rate": 180, "max": 250},
            3: {"name": "Gate 3 (NE)", "state": "open", "rate": 195, "max": 250},
            4: {"name": "Gate 4 (E)", "state": "open", "rate": 160, "max": 250},
            5: {"name": "Gate 5 (SE)", "state": "open", "rate": 135, "max": 250},
            6: {"name": "Gate 6 (S)", "state": "open", "rate": 175, "max": 250},
            7: {"name": "Gate 7 (SW)", "state": "open", "rate": 140, "max": 250},
            8: {"name": "Gate 8 (W)", "state": "open", "rate": 135, "max": 250}
        }
        
        self.responders = {
            "sec": {
                "id": "sec",
                "name": "Squad Alpha",
                "badge": "SEC",
                "x": 250, "y": 210,
                "homeX": 250, "homeY": 210,
                "targetX": 250, "targetY": 210,
                "status": "Standby • Control Room",
                "active": False,
                "timer": 0,
                "targetName": "Control Room"
            },
            "med": {
                "id": "med",
                "name": "First Responder 1",
                "badge": "MED",
                "x": 220, "y": 210,
                "homeX": 220, "homeY": 210,
                "targetX": 220, "targetY": 210,
                "status": "Standby • Medical Bay",
                "active": False,
                "timer": 0,
                "targetName": "Medical Bay"
            },
            "vol": {
                "id": "vol",
                "name": "Volunteer Echo",
                "badge": "VOL",
                "x": 280, "y": 210,
                "homeX": 280, "homeY": 210,
                "targetX": 280, "targetY": 210,
                "status": "Standby • Gate 2 Hub",
                "active": False,
                "timer": 0,
                "targetName": "Gate 2 Hub"
            }
        }
        
        self.logs = []
        self.gemini_api_key = None
        self.gemini_prediction = {
            "safety_score": 95,
            "risk_level": "LOW",
            "bottlenecks": [],
            "predictions": ["Arena circulation nominal. Turnstiles scan flow in standard ranges."],
            "action_recommendations": [
                {
                  "agent": "routing-agent",
                  "tool": "update_digital_signage",
                  "args": "PROCEED TO ALL EXIT GATES",
                  "rationale": "Facilitate steady ingress/egress nominal scans."
                }
            ],
            "advisories": [
                {"gate": i, "risk": "NOMINAL", "advice": "Continue nominal checkins."} for i in range(1, 9)
            ],
            "mode": "emulated",
            "timestamp": time.strftime("%H:%M:%S")
        }

    def add_log(self, msg: str, log_type: str = "info"):
        timestamp = time.strftime("%H:%M:%S")
        log_entry = {"time": timestamp, "msg": msg, "type": log_type}
        self.logs.insert(0, log_entry)
        if len(self.logs) > 30:
            self.logs.pop()

    def get_serialized_state(self):
        key_active = bool(self.gemini_api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"))
        return {
            "activeIncident": self.active_incident,
            "autopilot": self.autopilot,
            "attendance": self.attendance,
            "peakDensity": self.peak_density,
            "flowRate": self.flow_rate,
            "sectors": self.sectors,
            "gates": self.gates,
            "responders": self.responders,
            "logs": self.logs,
            "geminiPrediction": self.gemini_prediction,
            "hasGeminiKey": key_active
        }

state_store = TelemetryState()

# ==========================================
# 4. DECENRALIZED PYTHON AGENTS SYSTEM
# ==========================================

# --- AGENT A: GATE & TICKETING AGENT (The Inflow Specialist) ---
class GateAgent:
    def __init__(self):
        self.class_id = "gate-agent"

    def get_current_inflow_rate(self, gate_id: int) -> int:
        return state_store.gates[gate_id]["rate"]

    def predict_surge_window(self, current_rate: int) -> bool:
        return current_rate > 250

    async def run_analysis(self):
        if state_store.active_incident == "surge":
            await self.update_visual_hud("THINKING", "Analyzing Gate 3 throughput thresholds...")
            await asyncio.sleep(0.7)

            rate = self.get_current_inflow_rate(3)
            await self.update_visual_hud("CALLING", f"Calling get_current_inflow_rate(3)...", "get_current_inflow_rate")
            state_store.add_log(f"[GateAgent] Tool invoke: get_current_inflow_rate(3) -> {rate} scans/m")
            await asyncio.sleep(0.7)

            is_congested = self.predict_surge_window(rate)
            await self.update_visual_hud("CALLING", f"Calling predict_surge_window(Gate 3)...", "predict_surge_window")
            state_store.add_log("[GateAgent] Tool invoke: predict_surge_window() -> Surge predicted in Sector B exit", "warn")
            await asyncio.sleep(0.7)

            await self.update_visual_hud("ALERT", "ALERT: Gate 3 exit surge detected. Publishing event...")
            state_store.add_log("[GateAgent] Gate 3 congestion verified. Dispatching event details to Shared Event Bus.", "crit")

            # Publish event to Python event bus
            await event_bus.publish("GATE_CONGESTION", {"gateId": 3, "standId": "B", "rate": rate})
        else:
            await self.update_visual_hud("STANDBY", "Nominal. Gates 1-8 turnstiles scanning normally.")

    async def update_visual_hud(self, status: str, desc: str, active_tool: Optional[str] = None):
        msg = {
            "type": "AGENT_UPDATE",
            "agent": self.class_id,
            "status": status,
            "desc": desc,
            "activeTool": active_tool
        }
        await manager.broadcast(msg)

# --- AGENT B: DYNAMIC ROUTING AGENT (The Traffic Controller) ---
class RoutingAgent:
    def __init__(self):
        self.class_id = "routing-agent"
        # Bind Event Bus callbacks
        event_bus.subscribe("GATE_CONGESTION", self.handle_gate_congestion)
        event_bus.subscribe("WEATHER_EMERGENCY", self.handle_weather_emergency)
        event_bus.subscribe("THREAT_CORDON_ACTIVE", self.handle_threat_cordon)

    def calculate_bottleneck_index(self, concourse_id: str, occupancy: int) -> float:
        capacity = state_store.sectors[concourse_id]["capacity"]
        return round((occupancy / capacity) * 100, 1)

    async def update_digital_signage(self, location_id: str, instruction: str):
        # Alter physical LED billboard signage state
        event_msg = {
            "type": "SIGNAGE_UPDATE",
            "instruction": instruction,
            "style": "warning" if state_store.active_incident != "threat" else "emergency"
        }
        await manager.broadcast(event_msg)
        state_store.add_log(f"[RoutingAgent] Tool invoke: update_digital_signage({location_id}) -> LED updated.", "success")

    async def push_app_notification(self, sector: str, message: str):
        # Slide mobile phone app push notice
        push_msg = {
            "type": "MOBILE_PUSH",
            "sector": sector,
            "message": message
        }
        await manager.broadcast(push_msg)
        state_store.add_log(f"[RoutingAgent] Tool invoke: push_app_notification(Sector {sector}) -> Alert dispatched.", "success")

    async def update_visual_hud(self, status: str, desc: str, active_tool: Optional[str] = None):
        msg = {
            "type": "AGENT_UPDATE",
            "agent": self.class_id,
            "status": status,
            "desc": desc,
            "activeTool": active_tool
        }
        await manager.broadcast(msg)

    async def handle_gate_congestion(self, data: dict):
        await self.update_visual_hud("THINKING", f"Event: GATE_CONGESTION intercepted. Evaluating Sector {data['standId']}...")
        await asyncio.sleep(0.7)

        occ = state_store.sectors[data["standId"]]["occupancy"]
        density = self.calculate_bottleneck_index(data["standId"], occ)
        await self.update_visual_hud("CALLING", f"Calling calculate_bottleneck_index({data['standId']})...", "calculate_bottleneck_index")
        state_store.add_log(f"[RoutingAgent] Tool invoke: calculate_bottleneck_index({data['standId']}) -> {density}% occupancy")
        await asyncio.sleep(0.7)

        # Apply routing
        new_instruct = "STAND B: DEVIATE EXIT TO GATE 4"
        await self.update_digital_signage(data["standId"], new_instruct)
        await self.update_visual_hud("CALLING", "Calling update_digital_signage()...", "update_digital_signage")
        await asyncio.sleep(0.7)

        notice = "Congestion warning at Gate 3. Please deviate through Gate 4 exits."
        await self.push_app_notification(data["standId"], notice)
        await self.update_visual_hud("CALLING", "Calling push_app_notification()...", "push_app_notification")
        
        # Alter paths
        state_store.gates[3]["state"] = "open"
        state_store.gates[3]["rate"] = 180
        state_store.gates[4]["rate"] = 295

        await asyncio.sleep(0.7)
        await self.update_visual_hud("STANDBY", "NOMINAL. Stand B traffic successfully optimized to Gate 4.")
        state_store.add_log("[RoutingAgent] Crowd egress mitigation applied. Stand B traffic flows balanced.", "success")

        # Publish resolution event
        await event_bus.publish("SIGNAGE_ROUTING_COMPLETED", {"sector": "B", "targetGate": 4})

    async def handle_weather_emergency(self, data: dict):
        await self.update_visual_hud("THINKING", "Event: WEATHER_EMERGENCY intercepted. Coordinating covered lines...")
        await asyncio.sleep(0.7)

        await self.update_digital_signage("ALL", "WEATHER HAZARD: ESCAPE VIA METRO SHUTTLES")
        await self.update_visual_hud("CALLING", "Calling update_digital_signage(ALL)...", "update_digital_signage")
        await asyncio.sleep(0.7)

        await self.push_app_notification("ALL", "Rain alert: Covered shelter corridors opened towards Metro gate exits.")
        await self.update_visual_hud("CALLING", "Calling push_app_notification(ALL)...", "push_app_notification")
        
        await asyncio.sleep(0.7)
        await self.update_visual_hud("STANDBY", "NOMINAL. Weather escape routings locked in.")

    async def handle_threat_cordon(self, data: dict):
        await self.update_visual_hud("THINKING", f"Event: THREAT_CORDON_ACTIVE. Redirecting away from Gate {data['gateId']}...")
        await asyncio.sleep(0.7)

        await self.update_digital_signage("Gate 5", "DANGER: LOCKDOWN REGION E / AVOID GATE 5")
        await self.update_visual_hud("CALLING", "Calling update_digital_signage(Gate 5)...", "update_digital_signage")
        await asyncio.sleep(0.7)

        await self.push_app_notification("C", "ALERT: Gate 5 cordon active. Divert Sector C exits immediately to Gates 6 & 7.")
        await self.update_visual_hud("CALLING", "Calling push_app_notification(Sector C)...", "push_app_notification")

        # Mutate map boundaries
        state_store.gates[5]["state"] = "blocked"
        state_store.gates[5]["rate"] = 0

        await asyncio.sleep(0.7)
        await self.update_visual_hud("STANDBY", "NOMINAL. Traffic isolated around Gate 5 containment area.")

# --- AGENT C: INCIDENT & SAFETY AGENT (The First Responder) ---
class SafetyAgent:
    def __init__(self):
        self.class_id = "safety-agent"
        # Bind Event Bus listeners
        event_bus.subscribe("ANOMALY_THREAT_DETECTED", self.handle_threat_alert)
        event_bus.subscribe("ANOMALY_WEATHER_ALERT", self.handle_weather_alert)
        event_bus.subscribe("ANOMALY_MEDICAL_ALERT", self.handle_medical_alert)

    async def trigger_emergency_protocol(self, incident_type: str, sector_id: str):
        state_store.active_incident = incident_type
        
        if incident_type == "threat":
            state_store.sectors["C"]["state"] = "critical"
            state_store.sectors["D"]["state"] = "warning"
            state_store.gates[5]["state"] = "blocked"
            
        elif incident_type == "weather":
            for sid in state_store.sectors:
                state_store.sectors[sid]["state"] = "warning"
            state_store.flow_rate = 2240
            state_store.gates[2]["rate"] = 240
            state_store.gates[6]["rate"] = 245
            state_store.gates[7]["rate"] = 230
            
        elif incident_type == "medical":
            state_store.sectors["A"]["state"] = "warning"
            
        state_store.add_log(f"[SafetyAgent] Tool invoke: trigger_emergency_protocol({incident_type}) -> Limits overridden.", "crit")

    def dispatch_nearest_volunteers(self, squad_id: str, target_coords: dict):
        r = state_store.responders[squad_id]
        r["targetX"] = target_coords["x"]
        r["targetY"] = target_coords["y"]
        r["status"] = "En-route..."
        r["timer"] = 5
        r["targetName"] = target_coords["label"]
        
        state_store.add_log(f"[SafetyAgent] Tool invoke: dispatch_nearest_volunteers({squad_id}) -> Dispatch coordinates target locked.", "info")

        # Timer countdown callback
        async def run_countdown():
            count = 5
            while count > 0:
                await asyncio.sleep(1.0)
                count -= 1
                r["timer"] = count
                if count <= 0:
                    r["status"] = f"Active On Scene • {r['targetName']}"
                    r["active"] = True
                    r["x"] = r["targetX"]
                    r["y"] = r["targetY"]
                    state_store.add_log(f"[SafetyAgent] {r['name']} arrived at {r['targetName']}. Securing crowd safety.", "success")
                else:
                    r["status"] = f"En-route • ETA {count}s"
                await broadcast_telemetry()

        asyncio.create_task(run_countdown())

    async def update_visual_hud(self, status: str, desc: str, active_tool: Optional[str] = None):
        msg = {
            "type": "AGENT_UPDATE",
            "agent": self.class_id,
            "status": status,
            "desc": desc,
            "activeTool": active_tool
        }
        await manager.broadcast(msg)

    async def handle_threat_alert(self, data: dict):
        await self.update_visual_hud("THINKING", "Event: ANOMALY_THREAT intercepted. Formulating perimeter protocol...")
        await asyncio.sleep(0.7)

        await self.trigger_emergency_protocol("threat", str(data["gateId"]))
        await self.update_visual_hud("CALLING", "Calling trigger_emergency_protocol()...", "trigger_emergency_protocol")
        await asyncio.sleep(0.7)

        target = {"x": 395, "y": 315, "label": "Gate 5 (Incident Cordon)"}
        self.dispatch_nearest_volunteers("sec", target)
        await self.update_visual_hud("CALLING", "Calling dispatch_nearest_volunteers()...", "dispatch_nearest_volunteers")
        await asyncio.sleep(0.7)

        await self.update_visual_hud("ALERT", "CRITICAL. Lockdown isolation initiated around Gate 5 cordon.")
        state_store.add_log("[SafetyAgent] Cordon established. Security responders en-route. Directing Routing Agent to redirect exits.", "crit")

        # Publish to event bus to notify RoutingAgent
        await event_bus.publish("THREAT_CORDON_ACTIVE", {"gateId": 5})

    async def handle_weather_alert(self, data: dict):
        await self.update_visual_hud("THINKING", "Event: ANOMALY_WEATHER intercepted. Coordinating crowd shelters...")
        await asyncio.sleep(0.7)

        await self.trigger_emergency_protocol("weather", "all")
        await self.update_visual_hud("CALLING", "Calling trigger_emergency_protocol()...", "trigger_emergency_protocol")
        await asyncio.sleep(0.7)

        target = {"x": 350, "y": 210, "label": "Stand B Shelter"}
        self.dispatch_nearest_volunteers("vol", target)
        await self.update_visual_hud("CALLING", "Calling dispatch_nearest_volunteers()...", "dispatch_nearest_volunteers")
        await asyncio.sleep(0.7)

        await self.update_visual_hud("STANDBY", "NOMINAL. Weather shelter plans activated stadium-wide.")
        
        # Publish weather emergency onto event bus
        await event_bus.publish("WEATHER_EMERGENCY", {})

    async def handle_medical_alert(self, data: dict):
        await self.update_visual_hud("THINKING", "Event: ANOMALY_MEDICAL intercepted. Directing triage path...")
        await asyncio.sleep(0.7)

        await self.trigger_emergency_protocol("medical", data["standId"])
        await self.update_visual_hud("CALLING", "Calling trigger_emergency_protocol()...", "trigger_emergency_protocol")
        await asyncio.sleep(0.7)

        target = {"x": 250, "y": 130, "label": "Stand A (Cardiac patient)"}
        self.dispatch_nearest_volunteers("med", target)
        await self.update_visual_hud("CALLING", "Calling dispatch_nearest_volunteers()...", "dispatch_nearest_volunteers")
        await asyncio.sleep(0.7)

        await self.update_visual_hud("STANDBY", "NOMINAL. Emergency responders routed to Stand A patient location.")

# --- AGENT D: COGNITIVE PREDICTOR AGENT (Gemini Hub) ---
class GeminiAgent:
    def __init__(self):
        self.class_id = "gemini-agent"
        self.configured = False
        self.setup_sdk()

    def setup_sdk(self, dynamic_key: Optional[str] = None):
        key = dynamic_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if key:
            try:
                genai.configure(api_key=key)
                self.configured = True
                state_store.gemini_api_key = key
                return True
            except Exception as e:
                print(f"Error configuring Gemini SDK: {e}")
        return False

    async def update_visual_hud(self, status: str, desc: str, active_tool: Optional[str] = None):
        msg = {
            "type": "AGENT_UPDATE",
            "agent": self.class_id,
            "status": status,
            "desc": desc,
            "activeTool": active_tool
        }
        await manager.broadcast(msg)

    async def analyze_stadium(self) -> dict:
        key = state_store.gemini_api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        
        # Prepare telemetry snapshot representation
        attendance = state_store.attendance
        flow_rate = state_store.flow_rate
        peak_density = state_store.peak_density
        incident = state_store.active_incident
        
        sectors_str = ", ".join([f"{k} ({v['name']}): Occupancy={v['occupancy']}/{v['capacity']} (State={v['state']})" for k, v in state_store.sectors.items()])
        gates_str = ", ".join([f"Gate {k} ({v['name']}): State={v['state']}, Rate={v['rate']}/min" for k, v in state_store.gates.items()])
        responders_str = ", ".join([f"{v['name']} ({v['badge']}): Coords=({int(v['x'])}, {int(v['y'])}), Target={v['targetName']}, Status={v['status']}, Active={v['active']}" for k, v in state_store.responders.items()])

        # Build prompt
        prompt = f"""
You are the Aegis Arena AI Cognitive Safety Mesh Core.
Analyze the following real-time stadium safety metrics:
- Attendance: {attendance}
- Flow Rate: {flow_rate}/min
- Peak Concourse Density: {peak_density}%
- Active Incident: {incident}
- Stand Sectors: [{sectors_str}]
- Gate turnstile scanners: [{gates_str}]
- Responder Squads: [{responders_str}]

Predict potential crowd crushes, bottleneck locations, and responder dispatch efficiencies.
Recommend actionable directives utilizing the available tools for:
1. `routing-agent` (tools: `update_digital_signage(location_id, instruction)`, `push_app_notification(sector, message)`)
2. `safety-agent` (tools: `trigger_emergency_protocol(incident_type, sector_id)`, `dispatch_nearest_volunteers(squad_id, target_coords)`)

You MUST return a JSON response in the following strict schema:
{{
  "safety_score": integer (0 to 100 representing safety rating),
  "risk_level": "LOW" | "ELEVATED" | "SEVERE" | "CRITICAL",
  "bottlenecks": [string list of active flow bottlenecks],
  "predictions": [string list of short cognitive risk predictions / warnings],
  "action_recommendations": [
    {{
      "agent": "routing-agent" | "safety-agent",
      "tool": "update_digital_signage" | "push_app_notification" | "dispatch_nearest_volunteers",
      "args": string summary of action payload (e.g. "STAND B: DEVIATE EXIT TO GATE 4"),
      "rationale": string reason why this action mitigates the risk
    }}
  ],
  "advisories": [
    {{
      "gate": integer (1 to 8),
      "risk": "NOMINAL" | "BUSY" | "CONGESTED" | "CRITICAL",
      "advice": string recommendation for this specific gate turns scanning rate
    }}
  ]
}}
Do NOT include markdown syntax around the JSON output, return raw valid JSON.
"""
        await self.update_visual_hud("THINKING", "Executing multi-agent cognitive simulation...", "generative_prediction")
        state_store.add_log("[GeminiAgent] Initiated stadium safety cognitive audit.", "info")

        if key:
            try:
                # Run live Gemini
                loop = asyncio.get_event_loop()
                def call_gemini():
                    # Set the key explicitly on the thread
                    genai.configure(api_key=key)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response = model.generate_content(
                        prompt,
                        generation_config={"response_mime_type": "application/json"}
                    )
                    return response.text

                raw_json = await loop.run_in_executor(None, call_gemini)
                prediction = json.loads(raw_json)
                prediction["mode"] = "live"
                prediction["timestamp"] = time.strftime("%H:%M:%S")
                
                await self.update_visual_hud("STANDBY", "Real-time safety prediction completed successfully.")
                state_store.add_log("[GeminiAgent] ✦ Live Gemini Cognitive Audit completed.", "success")
                
                return prediction
            except Exception as e:
                state_store.add_log(f"[GeminiAgent] Live Gemini API error: {str(e)}. Falling back to Heuristic Emulation.", "warn")
                print(f"Gemini API error: {e}")
                
        # Heuristic Emulation fallback
        await asyncio.sleep(1.0) # Simulate thinking latency
        
        # Calculate heuristic values based on the telemetry state
        safety_score = 95
        risk_level = "LOW"
        bottlenecks = []
        predictions = ["Arena circulation nominal. Turnstiles scan flow in standard ranges."]
        action_recommendations = []
        advisories = []
        
        for k, v in state_store.gates.items():
            g_rate = v["rate"]
            g_state = v["state"]
            if g_state == "congested" or g_rate > 220:
                advisories.append({"gate": k, "risk": "CONGESTED", "advice": f"Throttle turnstile load at Gate {k} by 20%."})
            elif g_state == "blocked":
                advisories.append({"gate": k, "risk": "CRITICAL", "advice": f"GATE IS LOCKED. Re-route all Stand exits away from Gate {k}."})
            else:
                advisories.append({"gate": k, "risk": "NOMINAL", "advice": "Continue nominal checkins."})

        if incident == "surge":
            safety_score = 72
            risk_level = "ELEVATED"
            bottlenecks = ["Sector B Exit Concourse", "Gate 3 turns scanner"]
            predictions = [
                "Gate 3 turnstile scans exceeded 265/m scans. Severe congestion expected on Sector B exit in 3 minutes.",
                "Egress bottleneck in sector B can cause minor crowd push hazard."
            ]
            action_recommendations = [
                {
                  "agent": "routing-agent",
                  "tool": "update_digital_signage",
                  "args": "STAND B: DEVIATE EXIT TO GATE 4",
                  "rationale": "Redistribute egress scanning rate and prevent crush hazard at Gate 3 turns."
                },
                {
                  "agent": "routing-agent",
                  "tool": "push_app_notification",
                  "args": "Sector B warning: redirect through Gate 4 exits.",
                  "rationale": "Directly notify smartphone users of queue times."
                }
            ]
        elif incident == "weather":
            safety_score = 64
            risk_level = "SEVERE"
            bottlenecks = ["Metro corridor shuttle terminal", "Gate 2 Hub ingress"]
            predictions = [
                "Slippery ground hazard detected. Wet concourse corridors increase fall risks by 40%.",
                "Transit congestion under severe weather will delay stadium clearance by 20 minutes."
            ]
            action_recommendations = [
                {
                  "agent": "routing-agent",
                  "tool": "update_digital_signage",
                  "args": "WEATHER HAZARD: ESCAPE VIA METRO SHUTTLES",
                  "rationale": "Direct spectators safely to high-capacity public transport sheltering routes."
                },
                {
                  "agent": "safety-agent",
                  "tool": "dispatch_nearest_volunteers",
                  "args": "Volunteer Echo to Stand B Shelter",
                  "rationale": "Assure volunteer personnel coordinates evacuation vectors."
                }
            ]
        elif incident == "threat":
            safety_score = 35
            risk_level = "CRITICAL"
            bottlenecks = ["Gate 5 cordon zone", "Stand C main exit concourse"]
            predictions = [
                "Incident containment boundary active at Gate 5. Stand C crowd egress is blocked.",
                "Crush danger risk in Stand C exits if lockdown instructions are not clearly publicized."
            ]
            action_recommendations = [
                {
                  "agent": "routing-agent",
                  "tool": "update_digital_signage",
                  "args": "DANGER: LOCKDOWN REGION E / AVOID GATE 5",
                  "rationale": "Strictly segregate crowd egress paths from active security cordon."
                },
                {
                  "agent": "safety-agent",
                  "tool": "dispatch_nearest_volunteers",
                  "args": "Squad Alpha to Gate 5 (Incident Cordon)",
                  "rationale": "Deploy tactical security units to establish containment barriers."
                }
            ]
        elif incident == "medical":
            safety_score = 80
            risk_level = "ELEVATED"
            bottlenecks = ["Stand A medical triage access lane"]
            predictions = [
                "Responder ETA of 5s locks in triage path. Triage path must remain unobstructed.",
                "Slight bottleneck in Sector A turnstiles due to spectator curiosity slowing paths."
            ]
            action_recommendations = [
                {
                  "agent": "safety-agent",
                  "tool": "dispatch_nearest_volunteers",
                  "args": "First Responder 1 to Stand A",
                  "rationale": "Expedite medical responder intervention for cardiac distress incident."
                }
            ]
        else:
            action_recommendations = [
                {
                  "agent": "routing-agent",
                  "tool": "update_digital_signage",
                  "args": "PROCEED TO ALL EXIT GATES",
                  "rationale": "Facilitate steady ingress/egress nominal scans."
                }
            ]
            
        prediction = {
            "safety_score": safety_score,
            "risk_level": risk_level,
            "bottlenecks": bottlenecks,
            "predictions": predictions,
            "action_recommendations": action_recommendations,
            "advisories": advisories[:8],
            "mode": "emulated",
            "timestamp": time.strftime("%H:%M:%S")
        }
        
        await self.update_visual_hud("STANDBY", "Local safety prediction emulation completed.")
        state_store.add_log("[GeminiAgent] ⚙️ Emulated Cognitive Audit completed successfully.", "success")
        return prediction

# Instantiate Python Agent Mesh Instances
gate_agent_instance = GateAgent()
routing_agent_instance = RoutingAgent()
safety_agent_instance = SafetyAgent()
gemini_agent_instance = GeminiAgent()

# Helper to send telemetry states
async def broadcast_telemetry():
    await manager.broadcast({
        "type": "TELEMETRY",
        "state": state_store.get_serialized_state()
    })

# Background task runner for Gemini safety predictor
async def run_gemini_update():
    try:
        prediction = await gemini_agent_instance.analyze_stadium()
        state_store.gemini_prediction = prediction
        
        # Publish event to Python event bus
        await event_bus.publish("GEMINI_ANALYSIS_COMPLETED", prediction)
        
        # Auto-pilot integrations
        if state_store.autopilot:
            for rec in prediction.get("action_recommendations", []):
                agent = rec.get("agent")
                tool = rec.get("tool")
                args = rec.get("args")
                
                if agent == "routing-agent":
                    if tool == "update_digital_signage" and args:
                        if args != state_store.gemini_prediction.get("last_autopilot_signage"):
                            state_store.gemini_prediction["last_autopilot_signage"] = args
                            state_store.add_log(f"[AI Autopilot] Executing recommendation: routing_agent.update_digital_signage()", "info")
                            await routing_agent_instance.update_digital_signage("ALL", args)
                    elif tool == "push_app_notification" and args:
                        sector = "B" if "B" in args else ("C" if "C" in args else ("A" if "A" in args else "ALL"))
                        state_store.add_log(f"[AI Autopilot] Executing recommendation: routing_agent.push_app_notification()", "info")
                        await routing_agent_instance.push_app_notification(sector, f"AI Directives: {args}")
                elif agent == "safety-agent":
                    if tool == "dispatch_nearest_volunteers" and args:
                        squad = "sec" if "Alpha" in args or "sec" in args or "Squad" in args else ("med" if "med" in args or "Responder" in args or "distress" in args else "vol")
                        r = state_store.responders[squad]
                        if not r["active"] and r["timer"] == 0:
                            state_store.add_log(f"[AI Autopilot] Executing recommendation: safety_agent.dispatch_nearest_volunteers() for {r['name']}", "info")
                            target = {"x": 395, "y": 315, "label": "Gate 5 (Incident Cordon)"}
                            if squad == "med":
                                target = {"x": 250, "y": 130, "label": "Stand A (Cardiac patient)"}
                            elif squad == "vol":
                                target = {"x": 350, "y": 210, "label": "Stand B Shelter"}
                            safety_agent_instance.dispatch_nearest_volunteers(squad, target)
        
        await broadcast_telemetry()
    except Exception as ex:
        print(f"Error running Gemini update background task: {ex}")

# ==========================================
# 5. ASYNC BACKGROUND SIMULATION TICK LOOP
# ==========================================
async def simulation_tick_loop():
    await asyncio.sleep(2.0)
    print("FastAPI background simulation tick loop started.")
    tick_count = 0
    while True:
        try:
            # 1. Fluctuations under normal parameters
            if not state_store.active_incident:
                state_store.flow_rate = int(1200 + random.random() * 80)
                state_store.attendance = min(80000, state_store.attendance + random.randint(0, 4))
                
                for gid in state_store.gates:
                    state_store.gates[gid]["rate"] = int(130 + random.random() * 40)
                    
                if random.random() < 0.08:
                    gateNum = random.randint(1, 8)
                    state_store.add_log(f"[MeshInfo] Inflow scanner vectors nominal on Gate {gateNum}.")
            else:
                # Surge incident incremental ticks
                if state_store.active_incident == "surge":
                    state_store.sectors["B"]["state"] = "critical"
                    if state_store.gates[3]["state"] != "blocked":
                        state_store.gates[3]["state"] = "congested"
                        state_store.gates[3]["rate"] = min(420, state_store.gates[3]["rate"] + random.randint(10, 25))

            # 2. Drive Gate Tick Agent checking
            await gate_agent_instance.run_analysis()

            # 3. Animate responder coordinates linear translations
            for squad in state_store.responders.values():
                dx = squad["targetX"] - squad["x"]
                dy = squad["targetY"] - squad["y"]
                if abs(dx) > 1 or abs(dy) > 1:
                    squad["x"] += dx * 0.35
                    squad["y"] += dy * 0.35
                    # Snap coordinates if near
                    if abs(squad["targetX"] - squad["x"]) <= 1 and abs(squad["targetY"] - squad["y"]) <= 1:
                        squad["x"] = squad["targetX"]
                        squad["y"] = squad["targetY"]

            # 4. Broadcast state updates to WebSockets
            await broadcast_telemetry()

            # 5. Periodically run Gemini update (every 12 ticks / ~18 seconds)
            tick_count += 1
            if tick_count >= 12:
                tick_count = 0
                asyncio.create_task(run_gemini_update())

        except Exception as ex:
            print(f"Error in backend simulation tick: {ex}")
            
        await asyncio.sleep(1.5)

# Start background tick task on startup
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulation_tick_loop())
    state_store.add_log("FastAPI backend online. Stadium Agent Mesh live.", "success")
    # Run initial analysis
    asyncio.create_task(run_gemini_update())

# ==========================================
# 6. REST API CONTROLLERS
# ==========================================
class IncidentRequest(BaseModel):
    type: str

class DispatchRequest(BaseModel):
    squad_id: str

class GeminiConfigRequest(BaseModel):
    api_key: str

@app.post("/api/incident")
async def trigger_incident(req: IncidentRequest):
    itype = req.type
    state_store.active_incident = itype
    
    # Anomaly publish hook
    if itype == "surge":
        state_store.gates[3]["rate"] = 265
        state_store.add_log("[Operator Override] Post-match crowd exit surge simulated on Stand B.", "warn")
    elif itype == "weather":
        state_store.add_log("[Operator Override] Weather anomaly triggered: Severe weather warning.", "warn")
        await event_bus.publish("ANOMALY_WEATHER_ALERT", {"code": "STORM"})
    elif itype == "threat":
        state_store.add_log("[Operator Override] Threat alert triggered: suspicious baggage Gate 5.", "crit")
        await event_bus.publish("ANOMALY_THREAT_DETECTED", {"gateId": 5})
    elif itype == "medical":
        state_store.add_log("[Operator Override] Medical emergency triggered: Seat cardiac alert Stand A.", "crit")
        await event_bus.publish("ANOMALY_MEDICAL_ALERT", {"standId": "A"})
        
    await broadcast_telemetry()
    # Trigger immediate Gemini update task when an incident occurs
    asyncio.create_task(run_gemini_update())
    return {"status": "success", "triggered": itype}

@app.post("/api/gemini/analyze")
async def manual_gemini_analyze():
    await run_gemini_update()
    return {"status": "success", "prediction": state_store.gemini_prediction}

@app.post("/api/gemini/config")
async def configure_gemini_key(req: GeminiConfigRequest):
    key = req.api_key.strip()
    if not key:
        return {"status": "error", "message": "Key cannot be empty"}
    success = gemini_agent_instance.setup_sdk(key)
    if success:
        state_store.add_log("[GeminiAgent] ✦ Dynamic API Key registered successfully.", "success")
        # Trigger immediate run using new key
        asyncio.create_task(run_gemini_update())
        return {"status": "success"}
    return {"status": "error", "message": "Failed to configure Gemini SDK"}

@app.post("/api/dispatch")
async def manual_dispatch(req: DispatchRequest):
    sid = req.squad_id
    r = state_store.responders[sid]
    
    if r["active"]:
        # Recall unit
        state_store.add_log(f"[Manual Override] Recalling responder {r['name']} to base.", "info")
        r["active"] = False
        r["targetX"] = r["homeX"]
        r["targetY"] = r["homeY"]
        r["status"] = "Returning to base..."
        r["timer"] = 4
        r["targetName"] = "Control Room" if sid == "sec" else "Medical Bay"

        async def run_return():
            c = 4
            while c > 0:
                await asyncio.sleep(1.0)
                c -= 1
                r["timer"] = c
                if c <= 0:
                    r["status"] = f"Standby • {r['targetName']}"
                    r["x"] = r["homeX"]
                    r["y"] = r["homeY"]
                else:
                    r["status"] = f"Returning • ETA {c}s"
                await broadcast_telemetry()
        
        asyncio.create_task(run_return())
        
    else:
        # Move unit to manual patrol
        coords = {"x": 250, "y": 290, "label": "Stand C Patrol"} if sid == "sec" else {"x": 250, "y": 130, "label": "Stand A Patrol"}
        r["targetX"] = coords["x"]
        r["targetY"] = coords["y"]
        r["status"] = "En-route..."
        r["timer"] = 5
        r["targetName"] = coords["label"]
        
        state_store.add_log(f"[Manual Override] Dispatching {r['name']} to {coords['label']}.", "info")

        async def run_dispatch():
            c = 5
            while c > 0:
                await asyncio.sleep(1.0)
                c -= 1
                r["timer"] = c
                if c <= 0:
                    r["status"] = f"Active On Scene • {r['targetName']}"
                    r["active"] = True
                    r["x"] = r["targetX"]
                    r["y"] = r["targetY"]
                    state_store.add_log(f"[Manual Override] {r['name']} has arrived at patrol station.", "success")
                else:
                    r["status"] = f"En-route • ETA {c}s"
                await broadcast_telemetry()

        asyncio.create_task(run_dispatch())

    await broadcast_telemetry()
    return {"status": "success", "squad": sid}

@app.post("/api/autopilot")
async def toggle_autopilot(req: dict):
    state_store.autopilot = bool(req.get("autopilot", False))
    if state_store.autopilot:
        state_store.add_log("[MeshManager] AI Autopilot activated. System will automate routing checks.", "success")
    else:
        state_store.add_log("[MeshManager] AI Autopilot deactivated. Manual confirmation required.", "warn")
    await broadcast_telemetry()
    return {"status": "success", "autopilot": state_store.autopilot}

@app.post("/api/reset")
async def reset_mesh():
    state_store.active_incident = None
    state_store.flow_rate = 1240
    
    for sid in state_store.sectors:
        state_store.sectors[sid]["state"] = "safe"
    
    for gid in state_store.gates:
        state_store.gates[gid]["state"] = "open"
        state_store.gates[gid]["rate"] = 140
        
    for rid in state_store.responders:
        r = state_store.responders[rid]
        r["active"] = False
        r["timer"] = 0
        r["x"] = r["homeX"]
        r["y"] = r["homeY"]
        r["targetX"] = r["homeX"]
        r["targetY"] = r["homeY"]
        r["status"] = f"Standby • {r['targetName']}"

    state_store.add_log("[MeshManager] Stadium Agent Mesh reset successfully. All parameters restored.", "success")
    await broadcast_telemetry()
    return {"status": "success"}

# ==========================================
# 7. WEBSOCKET FRAME HANDLER
# ==========================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.class_connect(websocket)
    # Send initial state frame instantly upon connection
    await websocket.send_text(json.dumps({
        "type": "TELEMETRY",
        "state": state_store.get_serialized_state()
    }))
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.class_disconnect(websocket)

# ==========================================
# 8. UNIFIED STATIC ASSETS MOUNTING
# ==========================================
import os
from fastapi.staticfiles import StaticFiles

if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
elif os.path.exists("../frontend/dist"):
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
