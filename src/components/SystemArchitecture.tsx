import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Cpu, Database, Eye, Radar, MapPin, Camera, Zap, HardDrive } from "lucide-react";
import systemArchImage from "@/assets/system-architecture.png";

export default function SystemArchitecture() {
  const hardwareComponents = [
    {
      name: "Track Geometry",
      description: "LiDAR & Line Laser Systems",
      status: "active",
      icon: Radar,
      dataRate: "100 MB/s"
    },
    {
      name: "IMU/Gyro Unit",
      description: "Acceleration & Position",
      status: "active", 
      icon: Zap,
      dataRate: "5 KB/s"
    },
    {
      name: "Distance & Location",
      description: "GPS + RFID + Optical Encoder",
      status: "active",
      icon: MapPin,
      dataRate: "1 MB/s"
    },
    {
      name: "Video Recording",
      description: "4K High Frame Rate Camera",
      status: "active",
      icon: Camera,
      dataRate: "180 MB/s"
    }
  ];

  const softwareComponents = [
    {
      name: "Sensor Fusion Engine",
      description: "IMU & GPS Integration",
      status: "processing",
      icon: Cpu
    },
    {
      name: "AI Vision Processing",
      description: "Defect Detection & Classification",
      status: "processing",
      icon: Eye
    },
    {
      name: "TQI Calculations",
      description: "Track Quality Index Analysis",
      status: "processing",
      icon: Database
    },
    {
      name: "Data Storage",
      description: "SQL Database & Archive",
      status: "active",
      icon: HardDrive
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
                  <div key={index} className="flex items-center justify-between p-3 bg-muted/20 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-primary/10 rounded-md">
                        <Icon className="w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium text-sm">{component.name}</p>
                        <p className="text-xs text-muted-foreground">{component.description}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge className="bg-success/10 text-success border-success/20 mb-1">
                        Active
                      </Badge>
                      <p className="text-xs text-muted-foreground">{component.dataRate}</p>
                    </div>
                  </div>
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
                  <div key={index} className="flex items-center justify-between p-3 bg-muted/20 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-accent/10 rounded-md">
                        <Icon className="w-4 h-4 text-accent" />
                      </div>
                      <div>
                        <p className="font-medium text-sm">{component.name}</p>
                        <p className="text-xs text-muted-foreground">{component.description}</p>
                      </div>
                    </div>
                    <Badge className="bg-primary/10 text-primary border-primary/20">
                      {component.status === "processing" ? "Processing" : "Active"}
                    </Badge>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}