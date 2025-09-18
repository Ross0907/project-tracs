// Track geometry calculations based on EN 13848 and RDSO TM/IM/448 standards
// Sampling interval: 25cm as per requirements

export interface TrackGeometryData {
  chainage: number; // Distance along track in meters
  gauge: number; // Distance between rails (mm)
  leftRailLevel: number; // Left rail longitudinal level (mm)
  rightRailLevel: number; // Right rail longitudinal level (mm)
  leftRailAlignment: number; // Left rail alignment (mm)
  rightRailAlignment: number; // Right rail alignment (mm)
  crossLevel: number; // Banking/cant (mm)
  twist: number; // Differential cross level over 3m base (mm)
  unevenness: number; // Track unevenness (mm)
  verticalAcceleration: number; // m/s²
  lateralAcceleration: number; // m/s²
  speed: number; // km/h
  timestamp: Date;
}

export interface RailProfileData {
  chainage: number;
  leftRailWear: number; // mm
  rightRailWear: number; // mm
  railSection: string; // 52kg, 60kg, etc.
  wearPattern: 'normal' | 'corrugation' | 'head-check' | 'gauge-face';
  profileDeviation: number; // mm from standard profile
}

export interface ComplianceStatus {
  parameter: string;
  value: number;
  limit: number;
  status: 'compliant' | 'warning' | 'critical';
  standard: 'EN13848' | 'RDSO';
}

// EN 13848 Track Quality Limits (simplified for different track categories)
const EN13848_LIMITS = {
  gauge: { alert: 3, intervention: 5 }, // mm deviation from standard
  longitudinalLevel: { alert: 4, intervention: 8 }, // mm
  alignment: { alert: 4, intervention: 8 }, // mm
  crossLevel: { alert: 4, intervention: 8 }, // mm
  twist: { alert: 4, intervention: 8 }, // mm over 3m base
  unevenness: { alert: 4, intervention: 8 } // mm
};

// RDSO Limits (Indian Railways specific)
const RDSO_LIMITS = {
  gauge: { alert: 2, intervention: 4 }, // mm deviation
  speed: { maxOperational: 200 }, // km/h
  acceleration: { vertical: 2.5, lateral: 2.0 } // m/s²
};

export class TrackDataGenerator {
  private baseGauge = 1676; // mm (Indian broad gauge)
  private chainage = 0;
  
  generateRealtimeData(): TrackGeometryData {
    this.chainage += 0.25; // 25cm sampling interval
    
    // Simulate realistic track conditions with some variations
    const speed = 45 + Math.random() * 100; // 45-145 km/h
    const baseNoise = Math.random() * 0.5 - 0.25;
    
    // Track geometry parameters with realistic variations
    const gauge = this.baseGauge + (Math.random() * 4 - 2); // ±2mm variation
    const leftLevel = Math.sin(this.chainage * 0.01) * 2 + baseNoise;
    const rightLevel = Math.sin(this.chainage * 0.01 + 0.1) * 2 + baseNoise;
    const leftAlign = Math.cos(this.chainage * 0.008) * 1.5 + baseNoise;
    const rightAlign = Math.cos(this.chainage * 0.008 + 0.05) * 1.5 + baseNoise;
    
    const crossLevel = rightLevel - leftLevel;
    const twist = this.calculateTwist(crossLevel);
    const unevenness = Math.abs(leftLevel - rightLevel) * 0.5;
    
    // Dynamic parameters based on track quality and speed
    const speedFactor = speed / 100;
    const verticalAcc = (Math.abs(leftLevel) + Math.abs(rightLevel)) * 0.1 * speedFactor;
    const lateralAcc = Math.abs(crossLevel) * 0.08 * speedFactor;
    
    return {
      chainage: Math.round(this.chainage * 1000) / 1000,
      gauge: Math.round(gauge * 100) / 100,
      leftRailLevel: Math.round(leftLevel * 100) / 100,
      rightRailLevel: Math.round(rightLevel * 100) / 100,
      leftRailAlignment: Math.round(leftAlign * 100) / 100,
      rightRailAlignment: Math.round(rightAlign * 100) / 100,
      crossLevel: Math.round(crossLevel * 100) / 100,
      twist: Math.round(twist * 100) / 100,
      unevenness: Math.round(unevenness * 100) / 100,
      verticalAcceleration: Math.round(verticalAcc * 1000) / 1000,
      lateralAcceleration: Math.round(lateralAcc * 1000) / 1000,
      speed: Math.round(speed * 10) / 10,
      timestamp: new Date()
    };
  }
  
  generateRailProfile(): RailProfileData {
    const wearVariation = Math.random() * 0.8; // 0-0.8mm wear
    const sections = ['52kg', '60kg', '90UTS'];
    const patterns = ['normal', 'corrugation', 'head-check', 'gauge-face'] as const;
    
    return {
      chainage: this.chainage,
      leftRailWear: Math.round(wearVariation * 100) / 100,
      rightRailWear: Math.round((wearVariation + Math.random() * 0.3) * 100) / 100,
      railSection: sections[Math.floor(Math.random() * sections.length)],
      wearPattern: patterns[Math.floor(Math.random() * patterns.length)],
      profileDeviation: Math.round((Math.random() * 0.6 - 0.3) * 100) / 100
    };
  }
  
  private calculateTwist(crossLevel: number): number {
    // Twist calculation over 3m base (12 samples at 25cm intervals)
    // Simplified calculation for demonstration
    return crossLevel * 0.7 + (Math.random() * 0.4 - 0.2);
  }
  
  evaluateCompliance(data: TrackGeometryData): ComplianceStatus[] {
    const results: ComplianceStatus[] = [];
    
    // Gauge compliance
    const gaugeDeviation = Math.abs(data.gauge - this.baseGauge);
    results.push({
      parameter: 'Gauge',
      value: gaugeDeviation,
      limit: EN13848_LIMITS.gauge.alert,
      status: gaugeDeviation > EN13848_LIMITS.gauge.intervention ? 'critical' :
              gaugeDeviation > EN13848_LIMITS.gauge.alert ? 'warning' : 'compliant',
      standard: 'EN13848'
    });
    
    // Longitudinal Level
    const maxLevel = Math.max(Math.abs(data.leftRailLevel), Math.abs(data.rightRailLevel));
    results.push({
      parameter: 'Longitudinal Level',
      value: maxLevel,
      limit: EN13848_LIMITS.longitudinalLevel.alert,
      status: maxLevel > EN13848_LIMITS.longitudinalLevel.intervention ? 'critical' :
              maxLevel > EN13848_LIMITS.longitudinalLevel.alert ? 'warning' : 'compliant',
      standard: 'EN13848'
    });
    
    // Cross Level
    results.push({
      parameter: 'Cross Level',
      value: Math.abs(data.crossLevel),
      limit: EN13848_LIMITS.crossLevel.alert,
      status: Math.abs(data.crossLevel) > EN13848_LIMITS.crossLevel.intervention ? 'critical' :
              Math.abs(data.crossLevel) > EN13848_LIMITS.crossLevel.alert ? 'warning' : 'compliant',
      standard: 'EN13848'
    });
    
    // Twist
    results.push({
      parameter: 'Twist',
      value: Math.abs(data.twist),
      limit: EN13848_LIMITS.twist.alert,
      status: Math.abs(data.twist) > EN13848_LIMITS.twist.intervention ? 'critical' :
              Math.abs(data.twist) > EN13848_LIMITS.twist.alert ? 'warning' : 'compliant',
      standard: 'EN13848'
    });
    
    // Vertical Acceleration (RDSO)
    results.push({
      parameter: 'Vertical Acceleration',
      value: data.verticalAcceleration,
      limit: RDSO_LIMITS.acceleration.vertical,
      status: data.verticalAcceleration > RDSO_LIMITS.acceleration.vertical ? 'critical' : 'compliant',
      standard: 'RDSO'
    });
    
    return results;
  }
  
  // ICP-based rail profile registration (simplified implementation)
  registerRailProfile(measuredProfile: number[], standardProfile: number[]): {
    registrationError: number;
    wearMap: number[];
    confidence: number;
  } {
    // Simplified ICP registration simulation
    const registrationError = Math.random() * 0.1; // mm
    const confidence = Math.max(0.85, 1 - registrationError * 5);
    
    const wearMap = measuredProfile.map((point, index) => {
      const standard = standardProfile[index] || standardProfile[standardProfile.length - 1];
      return Math.max(0, standard - point); // Wear is material loss
    });
    
    return {
      registrationError: Math.round(registrationError * 1000) / 1000,
      wearMap,
      confidence: Math.round(confidence * 1000) / 1000
    };
  }
}

// Export singleton instance
export const trackDataGenerator = new TrackDataGenerator();