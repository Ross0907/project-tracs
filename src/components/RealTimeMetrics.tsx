import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, Gauge, MapPin, Clock, Zap, AlertTriangle } from "lucide-react";

export default function RealTimeMetrics() {
  const metrics = [
    {
      title: "Current Speed",
      value: "145",
      unit: "km/h",
      icon: Gauge,
      status: "normal",
      description: "Operating within limits"
    },
    {
      title: "Track Position",
      value: "KM 1247.5",
      unit: "chainage",
      icon: MapPin,
      status: "normal",
      description: "GPS + Axle encoder sync"
    },
    {
      title: "Sampling Rate",
      value: "25",
      unit: "cm",
      icon: Activity,
      status: "optimal",
      description: "Real-time acquisition"
    },
    {
      title: "System Uptime",
      value: "247.3",
      unit: "hours",
      icon: Clock,
      status: "excellent",
      description: "Continuous operation"
    },
    {
      title: "Processing Load",
      value: "67",
      unit: "%",
      icon: Zap,
      status: "normal",
      description: "AI vision processing"
    },
    {
      title: "Defects Detected",
      value: "3",
      unit: "alerts",
      icon: AlertTriangle,
      status: "warning",
      description: "Require inspection"
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "excellent": return "text-success";
      case "optimal": return "text-success";
      case "normal": return "text-primary";
      case "warning": return "text-warning";
      case "error": return "text-error";
      default: return "text-muted-foreground";
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "excellent": return <Badge className="bg-success/10 text-success border-success/20">Excellent</Badge>;
      case "optimal": return <Badge className="bg-success/10 text-success border-success/20">Optimal</Badge>;
      case "normal": return <Badge className="bg-primary/10 text-primary border-primary/20">Normal</Badge>;
      case "warning": return <Badge className="bg-warning/10 text-warning border-warning/20">Warning</Badge>;
      case "error": return <Badge className="bg-error/10 text-error border-error/20">Error</Badge>;
      default: return <Badge variant="outline">Unknown</Badge>;
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {metrics.map((metric, index) => {
        const Icon = metric.icon;
        return (
          <Card key={index} className="border-border/50 shadow-elegant hover:shadow-glow transition-all duration-300">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {metric.title}
                </CardTitle>
                <Icon className={`w-4 h-4 ${getStatusColor(metric.status)}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-baseline space-x-2">
                  <span className={`text-3xl font-bold ${getStatusColor(metric.status)}`}>
                    {metric.value}
                  </span>
                  <span className="text-sm text-muted-foreground">{metric.unit}</span>
                </div>
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted-foreground">{metric.description}</p>
                  {getStatusBadge(metric.status)}
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}