import { useState, useEffect, useRef } from 'react';
import { trackDataGenerator, TrackGeometryData, ComplianceStatus } from '@/utils/trackCalculations';

export function useRealtimeData() {
  const [currentData, setCurrentData] = useState<TrackGeometryData | null>(null);
  const [compliance, setCompliance] = useState<ComplianceStatus[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [historyData, setHistoryData] = useState<TrackGeometryData[]>([]);
  const intervalRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    // Simulate WebSocket connection
    setIsConnected(true);
    
    // Generate data every 100ms (simulating 25cm sampling at ~90 km/h)
    intervalRef.current = setInterval(() => {
      const newData = trackDataGenerator.generateRealtimeData();
      const newCompliance = trackDataGenerator.evaluateCompliance(newData);
      
      setCurrentData(newData);
      setCompliance(newCompliance);
      
      // Keep last 200 data points for charts
      setHistoryData(prev => {
        const updated = [...prev, newData];
        return updated.slice(-200);
      });
    }, 100);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      setIsConnected(false);
    };
  }, []);

  const criticalAlerts = compliance.filter(c => c.status === 'critical').length;
  const warningAlerts = compliance.filter(c => c.status === 'warning').length;
  const compliantCount = compliance.filter(c => c.status === 'compliant').length;

  return {
    currentData,
    compliance,
    historyData,
    isConnected,
    alerts: {
      critical: criticalAlerts,
      warning: warningAlerts,
      compliant: compliantCount
    }
  };
}
