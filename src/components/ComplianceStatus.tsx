import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Shield, CheckCircle, FileText, Award } from "lucide-react";

export default function ComplianceStatus() {
  const standards = [
    {
      name: "EN 13848 Part 1",
      description: "Track geometry quality assessment",
      compliance: 98,
      status: "compliant",
      lastCheck: "2024-01-15"
    },
    {
      name: "EN 13848 Part 2", 
      description: "Measuring systems requirements",
      compliance: 96,
      status: "compliant",
      lastCheck: "2024-01-15"
    },
    {
      name: "RDSO TM/IM/448 Rev. 1:2023",
      description: "Indian Railways specifications",
      compliance: 97,
      status: "compliant", 
      lastCheck: "2024-01-15"
    },
    {
      name: "ISO 9001:2015",
      description: "Quality management systems",
      compliance: 94,
      status: "compliant",
      lastCheck: "2024-01-12"
    }
  ];

  const certifications = [
    {
      title: "Railway Safety Certification",
      issuer: "RDSO",
      validUntil: "2025-12-31",
      status: "active"
    },
    {
      title: "ISO 9001:2015 Certificate",
      issuer: "Bureau Veritas",
      validUntil: "2025-06-30",
      status: "active"
    },
    {
      title: "NABL Calibration Certificate",
      issuer: "NABL India",
      validUntil: "2024-11-15",
      status: "expiring_soon"
    }
  ];

  return (
    <div className="space-y-6">
      <Card className="border-border/50 shadow-elegant">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Shield className="w-5 h-5 text-success" />
            <span>Standards Compliance Status</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {standards.map((standard, index) => (
              <div key={index} className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-foreground">{standard.name}</h4>
                    <p className="text-sm text-muted-foreground">{standard.description}</p>
                  </div>
                  <div className="text-right">
                    <Badge className="bg-success/10 text-success border-success/20 mb-1">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Compliant
                    </Badge>
                    <p className="text-xs text-muted-foreground">Last check: {standard.lastCheck}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Compliance Level</span>
                    <span className="font-medium">{standard.compliance}%</span>
                  </div>
                  <Progress value={standard.compliance} className="h-2" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="border-border/50 shadow-elegant">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Award className="w-5 h-5 text-primary" />
              <span>Active Certifications</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {certifications.map((cert, index) => (
                <div key={index} className="p-3 bg-muted/20 rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-medium text-foreground">{cert.title}</h4>
                    <Badge variant={cert.status === 'active' ? 'default' : 'secondary'}
                           className={cert.status === 'active' 
                             ? 'bg-success/10 text-success border-success/20' 
                             : 'bg-warning/10 text-warning border-warning/20'
                           }>
                      {cert.status === 'active' ? 'Active' : 'Expiring Soon'}
                    </Badge>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    <p>Issued by: {cert.issuer}</p>
                    <p>Valid until: {cert.validUntil}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50 shadow-elegant">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="w-5 h-5 text-accent" />
              <span>Documentation Status</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-3 bg-muted/20 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">Technical Documentation</span>
                  <Badge className="bg-success/10 text-success border-success/20">Complete</Badge>
                </div>
                <p className="text-sm text-muted-foreground">Hardware specifications, software architecture, user manuals</p>
              </div>
              
              <div className="p-3 bg-muted/20 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">Validation Reports</span>
                  <Badge className="bg-success/10 text-success border-success/20">Current</Badge>
                </div>
                <p className="text-sm text-muted-foreground">Standards compliance testing and field validation results</p>
              </div>
              
              <div className="p-3 bg-muted/20 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">Cost Analysis</span>
                  <Badge className="bg-primary/10 text-primary border-primary/20">Updated</Badge>
                </div>
                <p className="text-sm text-muted-foreground">Scalability roadmap and implementation cost breakdown</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}