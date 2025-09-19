import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Cpu, Database, Eye, Radar, MapPin, Camera, Zap, HardDrive, Info } from "lucide-react";
import systemArchImage from "@/assets/system-architecture.png";
import LaTeXFormula from "./LaTeXFormula";

export default function SystemArchitecture() {
  const hardwareComponents = [
    {
      name: "Track Geometry",
      description: "LiDAR & Line Laser Systems",
      status: "active",
      icon: Radar,
      dataRate: "100 MB/s",
      specifications: {
        accuracy: "±0.5mm lateral, ±0.2mm vertical",
        range: "±150mm lateral, ±100mm vertical",
        frequency: "20kHz laser scan rate",
        formula: "\\text{Geometric deviation} = \\sqrt{\\text{Lateral}^2 + \\text{Vertical}^2}",
        compliance: "EN 13848-1:2019, RDSO TM-448"
      }
    },
    {
      name: "IMU/Gyro Unit",
      description: "Acceleration & Position",
      status: "active", 
      icon: Zap,
      dataRate: "5 KB/s",
      specifications: {
        accuracy: "±0.01° roll/pitch, ±0.05° yaw",
        range: "±180° all axes",
        frequency: "100Hz sampling rate",
        formula: "\\omega = \\frac{\\Delta\\theta}{\\Delta t}, \\quad a = \\frac{\\Delta v}{\\Delta t}",
        compliance: "IEEE 952-1997 standard"
      }
    },
    {
      name: "Distance & Location",
      description: "GPS + RFID + Optical Encoder",
      status: "active",
      icon: MapPin,
      dataRate: "1 MB/s",
      specifications: {
        accuracy: "±1m GPS, ±0.1m RFID, ±0.01m Encoder",
        range: "Global GPS coverage",
        frequency: "10Hz GPS, Event-based RFID/Encoder",
        formula: "\\text{Position} = \\text{GPS}_{\\text{base}} + \\text{RFID}_{\\text{offset}} + \\text{Encoder}_{\\text{distance}}",
        compliance: "NMEA 0183, ISO 18000-6C"
      }
    },
    {
      name: "Video Recording",
      description: "4K High Frame Rate Camera",
      status: "active",
      icon: Camera,
      dataRate: "180 MB/s",
      specifications: {
        accuracy: "4K @ 60fps, 1080p @ 120fps",
        range: "3m field of view width",
        frequency: "Variable 30-120fps",
        formula: "\\text{Data rate} = \\text{Resolution} \\times \\text{FPS} \\times \\text{Color depth} \\times \\text{Compression ratio}",
        compliance: "H.265/HEVC encoding"
      }
    }
  ];

  const softwareComponents = [
    {
      name: "Sensor Fusion Engine",
      description: "IMU & GPS Integration",
      status: "processing",
      icon: Cpu,
      specifications: {
        algorithm: "Extended Kalman Filter (EKF)",
        accuracy: "Position fusion ±0.5m, Attitude ±0.02°",
        frequency: "50Hz processing rate",
        formula: "x_{k+1} = F \\cdot x_k + B \\cdot u_k + w_k, \\quad z_k = H \\cdot x_k + v_k",
        compliance: "ISO 8855:2011 vehicle dynamics"
      }
    },
    {
      name: "AI Vision Processing",
      description: "Defect Detection & Classification",
      status: "processing",
      icon: Eye,
      specifications: {
        algorithm: "CNN + YOLO v8 + ResNet-50",
        accuracy: "98.5% defect detection, 95.2% classification",
        frequency: "Real-time 30fps processing",
        formula: "\\text{Confidence} = \\text{softmax}(\\text{CNN}_{\\text{output}}), \\quad \\text{IoU} = \\frac{\\text{Area}_{\\text{overlap}}}{\\text{Area}_{\\text{union}}}",
        compliance: "EN 13848-5:2017 inspection methods"
      }
    },
    {
      name: "TQI Calculations",
      description: "Track Quality Index Analysis",
      status: "processing",
      icon: Database,
      specifications: {
        algorithm: "Weighted geometric mean calculation",
        accuracy: "±2% TQI variance",
        frequency: "Real-time with 200m window",
        formula: "\\text{TQI} = \\sqrt{\\frac{\\sigma_{\\text{Lat}}^2 + \\sigma_{\\text{Long}}^2 + \\sigma_{\\text{Vert}}^2 + \\sigma_{\\text{Gauge}}^2 + \\sigma_{\\text{Twist}}^2}{5}}",
        compliance: "EN 13848-6:2014 TQI standard"
      }
    },
    {
      name: "Data Storage",
      description: "SQL Database & Archive",
      status: "active",
      icon: HardDrive,
      specifications: {
        algorithm: "PostgreSQL with TimescaleDB",
        accuracy: "100% data integrity with checksums",
        frequency: "Continuous archival with compression",
        formula: "\\text{Storage efficiency} = \\frac{\\text{Compressed size}}{\\text{Original size}} \\times 100\\%",
        compliance: "ACID properties, ISO 27001"
      }
    }
  ];

  return (
    <div className="space-y-6">
      <Card className="border-border/50 shadow-elegant">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-primary" />
            <span>System Architecture Overview</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="aspect-video bg-muted/30 rounded-lg overflow-hidden border border-border/50">
            <img 
              src={systemArchImage} 
              alt="ITMS System Architecture Diagram showing hardware and software components"
              className="w-full h-full object-contain"
            />
          </div>
          <p className="text-sm text-muted-foreground mt-4">
            Comprehensive architecture featuring contactless sensors, real-time AI processing, and integrated data analysis
            compliant with EN 13848 and RDSO TM/IM/448 Rev. 1:2023 standards.
          </p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-border/50 shadow-elegant">
          <CardHeader>
            <CardTitle className="text-lg">Hardware Layer Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {hardwareComponents.map((component, index) => {
                const Icon = component.icon;
                return (
                  <Dialog key={index}>
                    <DialogTrigger asChild>
                      <div className="flex items-center justify-between p-3 bg-muted/20 rounded-lg cursor-pointer hover:bg-muted/30 transition-colors">
                        <div className="flex items-center space-x-3">
                          <div className="p-2 bg-primary/10 rounded-md">
                            <Icon className="w-4 h-4 text-primary" />
                          </div>
                          <div>
                            <p className="font-medium text-sm">{component.name}</p>
                            <p className="text-xs text-muted-foreground">{component.description}</p>
                          </div>
                        </div>
                        <div className="text-right flex items-center space-x-2">
                          <div>
                            <Badge className="bg-success/10 text-success border-success/20 mb-1">
                              Active
                            </Badge>
                            <p className="text-xs text-muted-foreground">{component.dataRate}</p>
                          </div>
                          <Info className="w-4 h-4 text-muted-foreground" />
                        </div>
                      </div>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl">
                      <DialogHeader>
                        <DialogTitle className="flex items-center space-x-2">
                          <Icon className="w-5 h-5 text-primary" />
                          <span>{component.name} - Technical Specifications</span>
                        </DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h4 className="font-semibold text-sm mb-2">Accuracy & Range</h4>
                            <p className="text-sm text-muted-foreground">{component.specifications.accuracy}</p>
                            <p className="text-sm text-muted-foreground mt-1">{component.specifications.range}</p>
                          </div>
                          <div>
                            <h4 className="font-semibold text-sm mb-2">Processing Rate</h4>
                            <p className="text-sm text-muted-foreground">{component.specifications.frequency}</p>
                            <p className="text-sm text-muted-foreground mt-1">Data Rate: {component.dataRate}</p>
                          </div>
                        </div>
                        <div>
                          <h4 className="font-semibold text-sm mb-2">Technical Formula</h4>
                          <div className="bg-muted p-4 rounded-lg">
                            <LaTeXFormula formula={component.specifications.formula} />
                          </div>
                        </div>
                        <div>
                          <h4 className="font-semibold text-sm mb-2">Compliance Standards</h4>
                          <p className="text-sm text-muted-foreground">{component.specifications.compliance}</p>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50 shadow-elegant">
          <CardHeader>
            <CardTitle className="text-lg">Software Layer Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {softwareComponents.map((component, index) => {
                const Icon = component.icon;
                return (
                  <Dialog key={index}>
                    <DialogTrigger asChild>
                      <div className="flex items-center justify-between p-3 bg-muted/20 rounded-lg cursor-pointer hover:bg-muted/30 transition-colors">
                        <div className="flex items-center space-x-3">
                          <div className="p-2 bg-accent/10 rounded-md">
                            <Icon className="w-4 h-4 text-accent" />
                          </div>
                          <div>
                            <p className="font-medium text-sm">{component.name}</p>
                            <p className="text-xs text-muted-foreground">{component.description}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge className="bg-primary/10 text-primary border-primary/20">
                            {component.status === "processing" ? "Processing" : "Active"}
                          </Badge>
                          <Info className="w-4 h-4 text-muted-foreground" />
                        </div>
                      </div>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl">
                      <DialogHeader>
                        <DialogTitle className="flex items-center space-x-2">
                          <Icon className="w-5 h-5 text-accent" />
                          <span>{component.name} - Technical Specifications</span>
                        </DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h4 className="font-semibold text-sm mb-2">Algorithm & Accuracy</h4>
                            <p className="text-sm text-muted-foreground">{component.specifications.algorithm}</p>
                            <p className="text-sm text-muted-foreground mt-1">{component.specifications.accuracy}</p>
                          </div>
                          <div>
                            <h4 className="font-semibold text-sm mb-2">Processing Rate</h4>
                            <p className="text-sm text-muted-foreground">{component.specifications.frequency}</p>
                          </div>
                        </div>
                        <div>
                          <h4 className="font-semibold text-sm mb-2">Technical Formula</h4>
                          <div className="bg-muted p-4 rounded-lg">
                            <LaTeXFormula formula={component.specifications.formula} />
                          </div>
                        </div>
                        <div>
                          <h4 className="font-semibold text-sm mb-2">Compliance Standards</h4>
                          <p className="text-sm text-muted-foreground">{component.specifications.compliance}</p>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}