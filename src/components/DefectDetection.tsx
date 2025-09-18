import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Eye, CheckCircle, XCircle, Clock, Download } from "lucide-react";

export default function DefectDetection() {
  const recentDetections = [
    {
      id: "D001",
      type: "Rail Surface Crack",
      severity: "high",
      location: "KM 1246.2",
      timestamp: "14:23:15",
      confidence: 94,
      status: "confirmed",
      description: "Longitudinal crack detected on left rail"
    },
    {
      id: "D002", 
      type: "Fastening Defect",
      severity: "medium",
      location: "KM 1245.8",
      timestamp: "14:21:42",
      confidence: 87,
      status: "pending",
      description: "Missing bolt detected in rail fastening"
    },
    {
      id: "D003",
      type: "Ballast Deformation",
      severity: "low",
      location: "KM 1244.5",
      timestamp: "14:19:33",
      confidence: 76,
      status: "reviewed",
      description: "Uneven ballast distribution observed"
    },
    {
      id: "D004",
      type: "Sleeper Crack",
      severity: "medium",
      location: "KM 1243.9",
      timestamp: "14:17:28",
      confidence: 91,
      status: "confirmed",
      description: "Hairline crack in concrete sleeper"
    }
  ];

  const aiStats = [
    { label: "Detection Accuracy", value: "94.2%", status: "excellent" },
    { label: "Processing Speed", value: "12ms", status: "optimal" },
    { label: "False Positives", value: "2.1%", status: "good" },
    { label: "Model Version", value: "v3.2.1", status: "current" }
  ];

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "high": return "text-error bg-error/10 border-error/20";
      case "medium": return "text-warning bg-warning/10 border-warning/20";
      case "low": return "text-success bg-success/10 border-success/20";
      default: return "text-muted-foreground bg-muted/10 border-border";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "confirmed": return <CheckCircle className="w-4 h-4 text-success" />;
      case "pending": return <Clock className="w-4 h-4 text-warning" />;
      case "reviewed": return <Eye className="w-4 h-4 text-primary" />;
      default: return <XCircle className="w-4 h-4 text-muted-foreground" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {aiStats.map((stat, index) => (
          <Card key={index} className="border-border/50 shadow-elegant">
            <CardContent className="p-4">
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">{stat.label}</p>
                <p className="text-2xl font-bold text-primary">{stat.value}</p>
                <Badge className="bg-success/10 text-success border-success/20">
                  {stat.status}
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-border/50 shadow-elegant">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-secondary" />
              <span>AI-Powered Defect Detection & Classification</span>
            </CardTitle>
            <div className="flex items-center space-x-2">
              <Badge className="bg-secondary/10 text-secondary border-secondary/20">
                Real-time Analysis
              </Badge>
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export Report
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentDetections.map((detection) => (
              <div key={detection.id} className="p-4 bg-muted/20 rounded-lg border border-border/50">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(detection.status)}
                    <div>
                      <h4 className="font-semibold text-foreground">{detection.type}</h4>
                      <p className="text-sm text-muted-foreground">{detection.description}</p>
                    </div>
                  </div>
                  <Badge className={getSeverityColor(detection.severity)}>
                    {detection.severity.toUpperCase()}
                  </Badge>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Location:</span>
                    <p className="font-medium">{detection.location}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Time:</span>
                    <p className="font-medium">{detection.timestamp}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Confidence:</span>
                    <p className="font-medium">{detection.confidence}%</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">ID:</span>
                    <p className="font-medium">{detection.id}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-6 p-4 bg-accent/5 rounded-lg border border-accent/20">
            <div className="flex items-center space-x-2 mb-2">
              <Eye className="w-4 h-4 text-accent" />
              <h4 className="font-medium text-accent">AI Vision Processing Status</h4>
            </div>
            <p className="text-sm text-muted-foreground">
              Deep learning models continuously analyze 4K video footage to detect rail surface defects, 
              fastening issues, ballast conditions, and sleeper integrity. Processing pipeline includes 
              noise reduction, feature extraction, and classification with confidence scoring.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}