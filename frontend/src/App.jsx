import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  ShieldAlert, 
  Map as MapIcon, 
  Cpu, 
  DoorOpen, 
  Route, 
  Network, 
  Radio, 
  Terminal, 
  Bell, 
  RotateCcw, 
  AlertTriangle, 
  CheckCircle, 
  Info, 
  Users, 
  CloudRain, 
  PackageSearch, 
  HeartPulse 
} from 'lucide-react';

export default function App() {
  const [wsConnected, setWsConnected] = useState(false);
  const [telemetry, setTelemetry] = useState({
    activeIncident: null,
    autopilot: false,
    attendance: 74820,
    peakDensity: 93.5,
    flowRate: 1240,
    sectors: {
      A: { name: "Stand A (North)", occupancy: 18450, capacity: 20000, state: "safe" },
      B: { name: "Stand B (East)", occupancy: 19120, capacity: 20000, state: "safe" },
      C: { name: "Stand C (South)", occupancy: 17850, capacity: 20000, state: "safe" },
      D: { name: "Stand D (West)", occupancy: 19400, capacity: 20000, state: "safe" }
    },
    gates: {
      1: { name: "Gate 1 (NW)", state: "open", rate: 120, max: 250 },
      2: { name: "Gate 2 (N)", state: "open", rate: 180, max: 250 },
      3: { name: "Gate 3 (NE)", state: "open", rate: 195, max: 250 },
      4: { name: "Gate 4 (E)", state: "open", rate: 160, max: 250 },
      5: { name: "Gate 5 (SE)", state: "open", rate: 135, max: 250 },
      6: { name: "Gate 6 (S)", state: "open", rate: 175, max: 250 },
      7: { name: "Gate 7 (SW)", state: "open", rate: 140, max: 250 },
      8: { name: "Gate 8 (W)", state: "open", rate: 135, max: 250 }
    },
    responders: {
      sec: { id: "sec", name: "Squad Alpha", badge: "SEC", x: 250, y: 210, homeX: 250, homeY: 210, targetX: 250, targetY: 210, status: "Standby • Control Room", active: false, timer: 0, targetName: "Control Room" },
      med: { id: "med", name: "First Responder 1", badge: "MED", x: 220, y: 210, homeX: 220, homeY: 210, targetX: 220, targetY: 210, status: "Standby • Medical Bay", active: false, timer: 0, targetName: "Medical Bay" },
      vol: { id: "vol", name: "Volunteer Echo", badge: "VOL", x: 280, y: 210, homeX: 280, homeY: 210, targetX: 280, targetY: 210, status: "Standby • Gate 2 Hub", active: false, timer: 0, targetName: "Gate 2 Hub" }
    },
    logs: []
  });

  // Agent HUD state
  const [agents, setAgents] = useState({
    'gate-agent': { status: "STANDBY", desc: "Idle. Monitoring turnstiles, ticket velocities and crowd entrances.", activeTool: null },
    'routing-agent': { status: "STANDBY", desc: "Idle. Tracking internal concourse densities & exit bottlenecks.", activeTool: null },
    'safety-agent': { status: "STANDBY", desc: "Idle. Processing anomalous sensors, transit alerts and emergency events.", activeTool: null }
  });

  // Event bus logs local stream
  const [eventBusStream, setEventBusStream] = useState([
    { event: "MESH_INITIATED", data: { status: "online" } }
  ]);

  // LED signage State
  const [signage, setSignage] = useState({
    text: "PROCEED TO ALL EXIT GATES",
    style: "normal"
  });

  // Smartphone notification Toast state
  const [phoneToast, setPhoneToast] = useState({
    active: false,
    sector: "",
    message: "",
    time: "11:20 AM"
  });

  // Detailed Map Overlay Popup Card
  const [overlayCard, setOverlayCard] = useState({
    visible: false,
    title: "",
    type: "", // 'sector' or 'gate'
    data: null
  });

  const eventBusRef = useRef(null);

  // Initialize WebSockets
  useEffect(() => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws");
    
    ws.onopen = () => {
      setWsConnected(true);
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "TELEMETRY") {
        setTelemetry(msg.state);
      } 
      
      else if (msg.type === "AGENT_UPDATE") {
        setAgents(prev => ({
          ...prev,
          [msg.agent]: {
            status: msg.status,
            desc: msg.desc,
            activeTool: msg.activeTool
          }
        }));
      } 
      
      else if (msg.type === "EVENT_BUS_LOG") {
        setEventBusStream(prev => {
          const updated = [...prev, { event: msg.event, data: msg.data }];
          if (updated.length > 15) updated.shift();
          return updated;
        });
      } 
      
      else if (msg.type === "SIGNAGE_UPDATE") {
        setSignage({
          text: msg.instruction,
          style: msg.style
        });
      } 
      
      else if (msg.type === "MOBILE_PUSH") {
        const now = new Date();
        const strTime = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        setPhoneToast({
          active: true,
          sector: msg.sector,
          message: msg.message,
          time: strTime
        });

        // Hide notification toast after 4.5s
        setTimeout(() => {
          setPhoneToast(prev => ({ ...prev, active: false }));
        }, 4500);
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  // REST controller integrations
  const triggerIncident = async (type) => {
    try {
      await fetch("http://127.0.0.1:8000/api/incident", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type })
      });
    } catch (e) {
      console.error("REST Error triggering incident:", e);
    }
  };

  const dispatchUnit = async (squadId) => {
    try {
      await fetch("http://127.0.0.1:8000/api/dispatch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ squad_id: squadId })
      });
    } catch (e) {
      console.error("REST Error dispatching unit:", e);
    }
  };

  const handleAutopilotToggle = async (e) => {
    const checked = e.target.checked;
    try {
      await fetch("http://127.0.0.1:8000/api/autopilot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ autopilot: checked })
      });
    } catch (e) {
      console.error("REST Error toggling autopilot:", e);
    }
  };

  const resetMesh = async () => {
    try {
      await fetch("http://127.0.0.1:8000/api/reset", { method: "POST" });
      setSignage({ text: "PROCEED TO ALL EXIT GATES", style: "normal" });
      setOverlayCard({ visible: false, title: "", type: "", data: null });
      setAgents({
        'gate-agent': { status: "STANDBY", desc: "Idle. Monitoring turnstiles, ticket velocities and crowd entrances.", activeTool: null },
        'routing-agent': { status: "STANDBY", desc: "Idle. Tracking internal concourse densities & exit bottlenecks.", activeTool: null },
        'safety-agent': { status: "STANDBY", desc: "Idle. Processing anomalous sensors, transit alerts and emergency events.", activeTool: null }
      });
    } catch (e) {
      console.error("REST Error resetting mesh:", e);
    }
  };

  // Map Click overlay handlers
  const handleSectorClick = (id) => {
    const s = telemetry.sectors[id];
    const cap = s.capacity;
    const occ = s.occupancy || 18000;
    const density = ((occ / cap) * 100).toFixed(1);
    
    setOverlayCard({
      visible: true,
      title: `${s.name} Sensor Report`,
      type: "sector",
      data: {
        cap, occ, density, state: s.state
      }
    });
  };

  const handleGateClick = (id) => {
    const g = telemetry.gates[id];
    const density = ((g.rate / g.max) * 100).toFixed(1);

    setOverlayCard({
      visible: true,
      title: `${g.name} Metrics`,
      type: "gate",
      data: {
        state: g.state,
        rate: g.rate,
        max: g.max,
        density
      }
    });
  };

  // Helper log types styling
  const getLogClass = (type) => {
    if (type === "crit") return "log-entry crit";
    if (type === "warn") return "log-entry warn";
    if (type === "success") return "log-entry success";
    return "log-entry info";
  };

  return (
    <>
      {/* Crimson Alert Overlay */}
      <div className={`hud-alert-overlay ${telemetry.activeIncident === 'threat' ? 'active' : ''}`} id="emergency-overlay"></div>

      {/* Smartphone Push Toast Alert */}
      <div className={`app-alert-toast ${phoneToast.active ? 'active' : ''}`}>
        <div className="phone-hud-header">
          <span className="phone-app-name">
            <Bell style={{ width: 10, height: 10, verticalAlign: 'middle', marginRight: 4 }} /> StadiumGuard
          </span>
          <span className="phone-time">{phoneToast.time}</span>
        </div>
        <div className="phone-alert-title">STADIUM DIRECTIVE: SECTOR {phoneToast.sector}</div>
        <div className="phone-alert-msg">{phoneToast.message}</div>
        <div className="phone-action-hint">Swipe down to view Live Route Map • Now</div>
      </div>

      <div className="app-container">
        
        {/* Header Dashboard HUD */}
        <header>
          <div className="brand-section">
            <div className="brand-logo">A</div>
            <div className="brand-title">
              <h1>AEGIS ARENA</h1>
              <div className="brand-subtitle">STADIUM AGENT MESH</div>
            </div>
          </div>

          <div className="header-stats">
            <div className="header-stat-card">
              <span className="header-stat-label">Event Match</span>
              <span className="header-stat-value">IND vs AUS - Grand Finale</span>
            </div>
            <div className="header-stat-card">
              <span className="header-stat-label">In-Stadium Attendance</span>
              <span className="header-stat-value">{telemetry.attendance.toLocaleString()} / 80,000</span>
            </div>
            <div className="header-stat-card">
              <span className="header-stat-label">Active Flow Rate</span>
              <span className="header-stat-value">{telemetry.flowRate.toLocaleString()} / min</span>
            </div>
            <div className="header-status-indicator">
              <span className={`pulse-dot ${
                telemetry.activeIncident === 'threat' ? 'critical' : 
                telemetry.activeIncident ? 'warning' : ''
              }`} id="system-status-dot"></span>
              <span>{
                telemetry.activeIncident === 'threat' ? 'SECURITY EMERGENCY' :
                telemetry.activeIncident ? 'WEATHER WARNING' : 'MESH NOMINAL'
              }</span>
            </div>
          </div>
        </header>

        {/* Dashboard Main layout grids */}
        <div className="dashboard-grid">
          
          {/* Left Column: Telemetry Meter and Simulators */}
          <div className="panel">
            <div className="panel-header">
              <h2 className="panel-title"><Activity size={14} /> Turnstile Operations</h2>
              <span className="panel-subtitle-tag">{wsConnected ? "LIVE MESH" : "DISCONNECTED"}</span>
            </div>
            <div className="panel-body">
              
              <div className="ticketing-grid">
                <div className="stat-box">
                  <div className="stat-label">Scans Today</div>
                  <div className="stat-value">{telemetry.attendance.toLocaleString()}</div>
                </div>
                <div className="stat-box purple">
                  <div className="stat-label">Est. Peak Density</div>
                  <div className="stat-value">{telemetry.peakDensity}%</div>
                </div>
                <div className={`stat-box ${
                  telemetry.gates[3].rate > 350 ? 'crimson' : 
                  telemetry.gates[3].rate > 220 ? 'amber' : 'green'
                }`}>
                  <div className="stat-label">G3 Turnstile Rate</div>
                  <div className="stat-value">{telemetry.gates[3].rate}/m</div>
                </div>
                <div className={`stat-box ${telemetry.activeIncident === 'weather' ? 'crimson' : 'green'}`}>
                  <div className="stat-label">Metro Transit Flow</div>
                  <div className="stat-value">{telemetry.activeIncident === 'weather' ? '890/m' : '512/m'}</div>
                </div>
              </div>

              {/* LED digital signage */}
              <div style={{ marginTop: '0.2rem' }}>
                <span className="stat-label" style={{ display: 'block', marginBottom: '0.3rem' }}>Digital LED Directional Signage</span>
                <div className="signage-display">
                  <div className={`signage-text ${
                    signage.style === 'emergency' ? 'emergency' :
                    signage.style === 'warning' ? 'warning' : ''
                  }`}>{signage.text}</div>
                </div>
              </div>

              <hr style={{ border: 'none', borderTop: '1px solid rgba(255, 255, 255, 0.05)', margin: '0.25rem 0' }} />

              {/* Incidents controller deck */}
              <div className="panel-title" style={{ marginBottom: '0.3rem' }}><ShieldAlert size={14} /> Incident Simulator</div>
              <div className="control-deck">
                <button className={`sim-button ${telemetry.activeIncident === 'surge' ? 'active' : ''}`} onClick={() => triggerIncident('surge')}>
                  <div className="sim-icon"><Users size={14} /></div>
                  <div className="sim-details">
                    <h4>Post-Match Exit Surge</h4>
                    <p>Simulates dense crowd exiting Stand B into Gate 3</p>
                  </div>
                </button>

                <button className={`sim-button ${telemetry.activeIncident === 'weather' ? 'active' : ''}`} onClick={() => triggerIncident('weather')}>
                  <div className="sim-icon"><CloudRain size={14} /></div>
                  <div className="sim-details">
                    <h4>Severe Weather Alert</h4>
                    <p>Triggers sudden downpour, slippery zones, transit rush</p>
                  </div>
                </button>

                <button className={`sim-button ${telemetry.activeIncident === 'threat' ? 'active' : ''}`} onClick={() => triggerIncident('threat')}>
                  <div className="sim-icon"><PackageSearch size={14} /></div>
                  <div className="sim-details">
                    <h4>Security Threat Event</h4>
                    <p>Unattended backpack near Gate 5. Sector C/D cordon.</p>
                  </div>
                </button>

                <button className={`sim-button ${telemetry.activeIncident === 'medical' ? 'active' : ''}`} onClick={() => triggerIncident('medical')}>
                  <div className="sim-icon"><HeartPulse size={14} /></div>
                  <div className="sim-details">
                    <h4>Medical Crisis Stand A</h4>
                    <p>Cardiac emergency Stand A. Open triage route lane.</p>
                  </div>
                </button>
              </div>

              <button className="btn-sec" onClick={resetMesh} style={{ width: '100%', marginTop: 'auto', padding: '0.4rem' }}>
                <RotateCcw size={12} style={{ verticalAlign: 'middle', marginRight: 4 }} /> Reset Mesh
              </button>
            </div>
          </div>

          {/* Center Column: High fidelity SVG Stadium Map */}
          <div className="panel map-panel">
            <div className="panel-header">
              <h2 className="panel-title"><MapIcon size={14} /> Interactive Crowd Density Blueprint</h2>
              <div className="map-legend">
                <div className="legend-item"><div className="legend-color" style={{ backgroundColor: 'var(--color-green)' }}></div><span>Safe (&lt;70%)</span></div>
                <div className="legend-item"><div className="legend-color" style={{ backgroundColor: 'var(--color-amber)' }}></div><span>Busy (70-90%)</span></div>
                <div className="legend-item"><div className="legend-color" style={{ backgroundColor: 'var(--color-crimson)' }}></div><span>Bottleneck (90%+)</span></div>
              </div>
            </div>

            <div className="map-toolbar">
              <div>Click Stand sectors or Exit Gates for local telemetry data</div>
              <div style={{ color: 'var(--color-cyan)' }}>SPEED: LIVE 1.0X</div>
            </div>

            <div className="map-wrapper">
              <svg viewBox="0 0 500 420" className="stadium-svg" xmlns="http://www.w3.org/2000/svg">
                
                {/* Stadium outer bounds */}
                <ellipse cx="250" cy="210" rx="200" ry="170" className="stadium-outline" />

                {/* Exit routing pathways with dash arrays animations */}
                {/* Stand A flows */}
                <path d="M 250 130 L 250 55" id="flow-A-G2" className={`exit-flow-path ${
                  telemetry.activeIncident === 'medical' ? 'rerouted' : 'active'
                }`} />
                <path d="M 180 135 Q 130 115 105 105" id="flow-A-G1" className={`exit-flow-path ${
                  telemetry.activeIncident === 'weather' ? 'rerouted' : ''
                }`} />
                <path d="M 320 135 Q 370 115 395 105" id="flow-A-G3" className="exit-flow-path" />

                {/* Stand B flows */}
                <path d="M 350 210 L 440 210" id="flow-B-G4" className={`exit-flow-path ${
                  telemetry.activeIncident === 'surge' ? 'rerouted' : 'active'
                }`} />
                <path d="M 340 160 Q 380 135 395 105" id="flow-B-G3" className={`exit-flow-path ${
                  telemetry.activeIncident === 'surge' ? '' : ''
                }`} />
                <path d="M 340 260 Q 380 285 395 315" id="flow-B-G5" className={`exit-flow-path ${
                  telemetry.activeIncident === 'threat' ? '' : ''
                }`} />

                {/* Stand C flows */}
                <path d="M 250 290 L 250 365" id="flow-C-G6" className={`exit-flow-path ${
                  telemetry.activeIncident === 'threat' ? 'rerouted' : 'active'
                }`} />
                <path d="M 320 285 Q 370 305 395 315" id="flow-C-G5" className={`exit-flow-path ${
                  telemetry.activeIncident === 'threat' ? '' : ''
                }`} />
                <path d="M 180 285 Q 130 305 105 315" id="flow-C-G7" className={`exit-flow-path ${
                  telemetry.activeIncident === 'threat' ? 'rerouted' :
                  telemetry.activeIncident === 'weather' ? 'rerouted' : ''
                }`} />

                {/* Stand D flows */}
                <path d="M 150 210 L 60 210" id="flow-D-G8" className="exit-flow-path active" />
                <path d="M 160 160 Q 120 135 105 105" id="flow-D-G1" className="exit-flow-path" />
                <path d="M 160 260 Q 120 285 105 315" id="flow-D-G7" className={`exit-flow-path ${
                  telemetry.activeIncident === 'weather' ? 'rerouted' : ''
                }`} />

                {/* Cricket Pitch */}
                <ellipse cx="250" cy="210" rx="55" ry="45" className="pitch" />
                <ellipse cx="250" cy="210" rx="30" ry="25" className="pitch-lines" />
                <line x1="250" y1="195" x2="250" y2="225" className="pitch-lines" />

                {/* Sectors/Stands */}
                <path d="M 120 120 A 180 150 0 0 1 380 120 L 340 145 A 130 110 0 0 0 160 145 Z" 
                      className={`stadium-sector sector-level-${
                        telemetry.sectors.A.state === 'critical' ? 'crit' : 
                        telemetry.sectors.A.state === 'warning' ? 'warn' : 'safe'
                      }`} onClick={() => handleSectorClick('A')} />
                
                <path d="M 380 120 A 180 150 0 0 1 380 300 L 340 275 A 130 110 0 0 0 340 145 Z" 
                      className={`stadium-sector sector-level-${
                        telemetry.sectors.B.state === 'critical' ? 'crit' : 
                        telemetry.sectors.B.state === 'warning' ? 'warn' : 'safe'
                      }`} onClick={() => handleSectorClick('B')} />
                
                <path d="M 380 300 A 180 150 0 0 1 120 300 L 160 275 A 130 110 0 0 0 340 275 Z" 
                      className={`stadium-sector sector-level-${
                        telemetry.sectors.C.state === 'critical' ? 'crit' : 
                        telemetry.sectors.C.state === 'warning' ? 'warn' : 'safe'
                      }`} onClick={() => handleSectorClick('C')} />
                
                <path d="M 120 300 A 180 150 0 0 1 120 120 L 160 145 A 130 110 0 0 0 160 275 Z" 
                      className={`stadium-sector sector-level-${
                        telemetry.sectors.D.state === 'critical' ? 'crit' : 
                        telemetry.sectors.D.state === 'warning' ? 'warn' : 'safe'
                      }`} onClick={() => handleSectorClick('D')} />

                {/* Stand Labels */}
                <text x="250" y="105" fill="#fff" fontFamily="Orbitron" fontSize="10" fontWeight="700" textAnchor="middle" pointerEvents="none">STAND A</text>
                <text x="390" y="215" fill="#fff" fontFamily="Orbitron" fontSize="10" fontWeight="700" textAnchor="middle" pointerEvents="none">STAND B</text>
                <text x="250" y="325" fill="#fff" fontFamily="Orbitron" fontSize="10" fontWeight="700" textAnchor="middle" pointer-events="none">STAND C</text>
                <text x="110" y="215" fill="#fff" fontFamily="Orbitron" fontSize="10" fontWeight="700" textAnchor="middle" pointer-events="none">STAND D</text>

                {/* Threat packages icon overlay */}
                {telemetry.activeIncident === 'threat' && (
                  <g className="map-threat-marker">
                    <circle cx="395" cy="315" r="18" fill="rgba(255, 0, 85, 0.2)" stroke="var(--color-crimson)" strokeWidth="1.5" />
                    <path d="M 395 303 L 385 323 L 405 323 Z" fill="var(--color-crimson)" />
                    <text x="395" y="321" fill="#fff" fontFamily="Inter" fontSize="9" fontWeight="900" textAnchor="middle">!</text>
                  </g>
                )}

                {/* Gates Nodes */}
                <g onClick={() => handleGateClick(1)}>
                  <circle cx="105" cy="105" r="10" className={`map-gate gate-${telemetry.gates[1].state}`} />
                  <text x="105" y="93" fill="#fff" fontFamily="Orbitron" fontSize="8" textAnchor="middle">G1</text>
                </g>
                <g onClick={() => handleGateClick(2)}>
                  <circle cx="250" cy="55" r="10" className={`map-gate gate-${telemetry.gates[2].state}`} />
                  <text x="250" y="43" fill="#fff" fontFamily="Orbitron" fontSize="8" textAnchor="middle">G2</text>
                </g>
                <g onClick={() => handleGateClick(3)}>
                  <circle cx="395" cy="105" r="10" className={`map-gate gate-${telemetry.gates[3].state}`} />
                  <text x="395" y="93" fill="#fff" fontFamily="Orbitron" fontSize="8" textAnchor="middle">G3</text>
                </g>
                <g onClick={() => handleGateClick(4)}>
                  <circle cx="440" cy="210" r="10" className={`map-gate gate-${telemetry.gates[4].state}`} />
                  <text x="455" y="214" fill="#fff" fontFamily="Orbitron" fontSize="8" textAnchor="start">G4</text>
                </g>
                <g onClick={() => handleGateClick(5)}>
                  <circle cx="395" cy="315" r="10" className={`map-gate gate-${telemetry.gates[5].state}`} />
                  <text x="395" y="333" fill="#fff" fontFamily="Orbitron" fontSize="8" textAnchor="middle">G5</text>
                </g>
                <g onClick={() => handleGateClick(6)}>
                  <circle cx="250" cy="365" r="10" className={`map-gate gate-${telemetry.gates[6].state}`} />
                  <text x="250" y="383" fill="#fff" fontFamily="Orbitron" fontSize="8" textAnchor="middle">G6</text>
                </g>
                <g onClick={() => handleGateClick(7)}>
                  <circle cx="105" cy="315" r="10" className={`map-gate gate-${telemetry.gates[7].state}`} />
                  <text x="105" y="333" fill="#fff" fontFamily="Orbitron" fontSize="8" textAnchor="middle">G7</text>
                </g>
                <g onClick={() => handleGateClick(8)}>
                  <circle cx="60" cy="210" r="10" className={`map-gate gate-${telemetry.gates[8].state}`} />
                  <text x="45" y="214" fill="#fff" fontFamily="Orbitron" fontSize="8" textAnchor="end">G8</text>
                </g>

                {/* Moving Responders Tokens on map using React transitions state */}
                <g className="responder-node sec" style={{ transform: `translate(${telemetry.responders.sec.x}px, ${telemetry.responders.sec.y}px)` }}>
                  <circle cx="0" cy="0" r="16" className="responder-radar" />
                  <circle cx="0" cy="0" r="8" className="responder-dot" />
                  <text x="0" y="3" fill="#fff" fontFamily="Orbitron" fontSize="8" fontWeight="900" textAnchor="middle" pointerEvents="none">S</text>
                </g>

                <g className="responder-node med" style={{ transform: `translate(${telemetry.responders.med.x}px, ${telemetry.responders.med.y}px)` }}>
                  <circle cx="0" cy="0" r="16" className="responder-radar" />
                  <circle cx="0" cy="0" r="8" className="responder-dot" />
                  <text x="0" y="3" fill="#fff" fontFamily="Orbitron" fontSize="8" fontWeight="900" textAnchor="middle" pointer-events="none">M</text>
                </g>

                <g className="responder-node vol" style={{ transform: `translate(${telemetry.responders.vol.x}px, ${telemetry.responders.vol.y}px)` }}>
                  <circle cx="0" cy="0" r="16" className="responder-radar" />
                  <circle cx="0" cy="0" r="8" className="responder-dot" />
                  <text x="0" y="3" fill="#fff" fontFamily="Orbitron" fontSize="8" fontWeight="900" textAnchor="middle" pointer-events="none">V</text>
                </g>

              </svg>

              {/* Detailed Overlay Card */}
              {overlayCard.visible && (
                <div className="map-overlay-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.4rem' }}>
                    <h3 style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: '#fff' }}>{overlayCard.title}</h3>
                    <button onClick={() => setOverlayCard(prev => ({ ...prev, visible: false }))} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.8rem' }}>×</button>
                  </div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    {overlayCard.type === 'sector' && overlayCard.data && (
                      <>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Capacity Limit:</span><strong>{overlayCard.data.cap.toLocaleString()} seats</strong></div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Occupied Seats:</span><strong>{overlayCard.data.occ.toLocaleString()}</strong></div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Density Index:</span><strong style={{ color: overlayCard.data.state === 'critical' ? 'var(--color-crimson)' : overlayCard.data.state === 'warning' ? 'var(--color-amber)' : 'var(--color-green)' }}>{overlayCard.data.density}%</strong></div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Sensors State:</span><strong>Active & Connected</strong></div>
                      </>
                    )}
                    {overlayCard.type === 'gate' && overlayCard.data && (
                      <>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Scanner State:</span><strong style={{ color: overlayCard.data.state === 'blocked' ? 'var(--color-crimson)' : overlayCard.data.state === 'congested' ? 'var(--color-amber)' : 'var(--color-cyan)' }}>{overlayCard.data.state.toUpperCase()}</strong></div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Flow Rate:</span><strong>{overlayCard.data.rate} scans/m</strong></div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Max Limit:</span><strong>{overlayCard.data.max} scans/m</strong></div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Load Level:</span><strong>{overlayCard.data.density}%</strong></div>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: React Agent Mesh control dashboard */}
          <div className="panel">
            <div className="panel-header" style={{ background: 'rgba(157, 78, 221, 0.05)', borderBottom: '1px solid rgba(157, 78, 221, 0.15)' }}>
              <h2 className="panel-title" style={{ color: '#e0aaff' }}><Cpu size={14} style={{ color: 'var(--color-purple)' }} /> Agent Mesh Control Console</h2>
              <label className="autopilot-switch">
                <span>AUTOPILOT</span>
                <div className="switch">
                  <input type="checkbox" checked={telemetry.autopilot} onChange={handleAutopilotToggle} />
                  <span className="slider"></span>
                </div>
              </label>
            </div>

            <div className="panel-body" style={{ gap: '0.6rem', paddingBottom: '0.4rem' }}>
              <div className="agent-mesh-console">
                
                {/* Gate Agent Card */}
                <div className="agent-node-card gate-agent">
                  <div className="agent-node-header">
                    <span className="agent-name-tag"><DoorOpen size={12} /> Gate & Ticketing Agent</span>
                    <span className={`agent-status-badge ${agents['gate-agent'].status.toLowerCase()}`}>{agents['gate-agent'].status}</span>
                  </div>
                  <div className="agent-action-desc">{agents['gate-agent'].desc}</div>
                  <div className="agent-tools-container">
                    <span className={`tool-badge ${agents['gate-agent'].activeTool === 'get_current_inflow_rate' ? 'active-call' : ''}`} id="tool-get_current_inflow_rate">get_current_inflow_rate()</span>
                    <span className={`tool-badge ${agents['gate-agent'].activeTool === 'predict_surge_window' ? 'active-call' : ''}`} id="tool-predict_surge_window">predict_surge_window()</span>
                  </div>
                </div>

                {/* Routing Agent Card */}
                <div className="agent-node-card routing-agent">
                  <div className="agent-node-header">
                    <span className="agent-name-tag"><Route size={12} /> Dynamic Routing Agent</span>
                    <span className={`agent-status-badge ${agents['routing-agent'].status.toLowerCase()}`}>{agents['routing-agent'].status}</span>
                  </div>
                  <div className="agent-action-desc">{agents['routing-agent'].desc}</div>
                  <div className="agent-tools-container">
                    <span className={`tool-badge ${agents['routing-agent'].activeTool === 'calculate_bottleneck_index' ? 'active-call' : ''}`} id="tool-calculate_bottleneck_index">calculate_bottleneck_index()</span>
                    <span className={`tool-badge ${agents['routing-agent'].activeTool === 'update_digital_signage' ? 'active-call' : ''}`} id="tool-update_digital_signage">update_digital_signage()</span>
                    <span className={`tool-badge ${agents['routing-agent'].activeTool === 'push_app_notification' ? 'active-call' : ''}`} id="tool-push_app_notification">push_app_notification()</span>
                  </div>
                </div>

                {/* Safety Agent Card */}
                <div className="agent-node-card safety-agent">
                  <div className="agent-node-header">
                    <span className="agent-name-tag"><ShieldAlert size={12} /> Incident & Safety Agent</span>
                    <span className={`agent-status-badge ${agents['safety-agent'].status.toLowerCase()}`}>{agents['safety-agent'].status}</span>
                  </div>
                  <div className="agent-action-desc">{agents['safety-agent'].desc}</div>
                  <div className="agent-tools-container">
                    <span className={`tool-badge ${agents['safety-agent'].activeTool === 'trigger_emergency_protocol' ? 'active-call' : ''}`} id="tool-trigger_emergency_protocol">trigger_emergency_protocol()</span>
                    <span className={`tool-badge ${agents['safety-agent'].activeTool === 'dispatch_nearest_volunteers' ? 'active-call' : ''}`} id="tool-dispatch_nearest_volunteers">dispatch_nearest_volunteers()</span>
                  </div>
                </div>

              </div>
            </div>

            {/* Shared Event Bus HUD Log */}
            <div className="panel-header" style={{ borderTop: '1px solid rgba(255, 255, 255, 0.05)', paddingTop: '0.4rem', paddingBottom: '0.4rem' }}>
              <h2 className="panel-title"><Network size={14} /> Shared Event Bus Stream</h2>
              <span className="pulse-dot" style={{ backgroundColor: 'var(--color-purple)', boxShadow: '0 0 6px var(--color-purple-glow)', width: 6, height: 6 }}></span>
            </div>
            <div style={{ padding: '0.5rem 1rem 0.3rem 1rem' }}>
              <div className="event-bus-scroller">
                {eventBusStream.map((ev, index) => (
                  <div className="event-bus-row" key={index}>
                    <span className="pub-tag">[BUS]</span>
                    <span className="event-name">{ev.event}</span>
                    <span className="event-data">{JSON.stringify(ev.data)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Manual Responders dispatches */}
            <div className="panel-header" style={{ borderTop: '1px solid rgba(255, 255, 255, 0.05)', paddingTop: '0.4rem', paddingBottom: '0.4rem' }}>
              <h2 className="panel-title"><Radio size={14} /> Manual Dispatcher</h2>
              <span className="panel-subtitle-tag">OVERRIDE</span>
            </div>
            <div className="panel-body" style={{ paddingTop: '0.4rem', paddingBottom: '0.4rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: '0 0 auto' }}>
              <div className="dispatcher-center">
                <div className="squad-card">
                  <div className="squad-info">
                    <div className="squad-badge sec">SEC</div>
                    <div className="squad-meta">
                      <h4>Squad Alpha</h4>
                      <p>{telemetry.responders.sec.status}</p>
                    </div>
                  </div>
                  <button className="dispatch-btn" disabled={telemetry.responders.sec.timer > 0} onClick={() => dispatchUnit('sec')}>
                    {telemetry.responders.sec.active ? "RETURNING" : telemetry.responders.sec.timer > 0 ? `${telemetry.responders.sec.timer}s` : "DISPATCH"}
                  </button>
                </div>

                <div className="squad-card">
                  <div className="squad-info">
                    <div className="squad-badge med">MED</div>
                    <div className="squad-meta">
                      <h4>First Responder 1</h4>
                      <p>{telemetry.responders.med.status}</p>
                    </div>
                  </div>
                  <button className="dispatch-btn" disabled={telemetry.responders.med.timer > 0} onClick={() => dispatchUnit('med')}>
                    {telemetry.responders.med.active ? "RETURNING" : telemetry.responders.med.timer > 0 ? `${telemetry.responders.med.timer}s` : "DISPATCH"}
                  </button>
                </div>
              </div>
            </div>

            {/* Live logs ticker */}
            <div className="panel-header" style={{ borderTop: '1px solid rgba(255, 255, 255, 0.05)', paddingTop: '0.4rem', paddingBottom: '0.4rem' }}>
              <h2 className="panel-title"><Terminal size={14} /> Command Log Ticker</h2>
              <span className="pulse-dot" style={{ width: 5, height: 5 }}></span>
            </div>
            <div className="panel-body logs-panel" style={{ paddingTop: '0.4rem' }}>
              <div className="logs-container">
                {telemetry.logs.map((log, index) => (
                  <div className={getLogClass(log.type)} key={index}>
                    <span className="log-time">[{log.time}]</span>
                    <span className="log-msg">{log.msg}</span>
                  </div>
                ))}
              </div>
            </div>

          </div>

        </div>

      </div>
    </>
  );
}
