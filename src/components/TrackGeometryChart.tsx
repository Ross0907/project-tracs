import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts";
import { TrendingUp, AlertTriangle, CheckCircle } from "lucide-react";

export default function TrackGeometryChart() {
  // Simulated real-time track geometry data
  const geometryData = [
    { chainage: 1245.0, gauge: 1435.2, alignment: 2.1, unevenness: 1.8, twist: 0.9, crossLevel: 1.2 },
    { chainage: 1245.5, gauge: 1434.8, alignment: 2.3, unevenness: 2.1, twist: 1.1, crossLevel: 1.4 },
    { chainage: 1246.0, gauge: 1435.1, alignment: 1.9, unevenness: 1.6, twist: 0.8, crossLevel: 1.0 },
    { chainage: 1246.5, gauge: 1435.3, alignment: 2.2, unevenness: 1.9, twist: 1.0, crossLevel: 1.3 },
    { chainage: 1247.0, gauge: 1434.9, alignment: 2.4, unevenness: 2.2, twist: 1.2, crossLevel: 1.5 },
    { chainage: 1247.5, gauge: 1435.0, alignment: 2.0, unevenness: 1.7, twist: 0.9, crossLevel: 1.1 },
  ];

  const parameters = [
    {
      name: "Track Gauge",
      value: "1435.0 mm",
      status: "normal",
      tolerance: "±3mm",
      icon: CheckCircle
    },
    {
      name: "Alignment",
      value: "2.0 mm",
      status: "normal", 
      tolerance: "±6mm",
      icon: CheckCircle
    },
    {
      name: "Unevenness",
      value: "1.7 mm",
      status: "normal",
      tolerance: "±4mm", 
      icon: CheckCircle
    },
    {
      name: "Cross Level",
      value: "1.1 mm",
      status: "warning",
      tolerance: "±3mm",
      icon: AlertTriangle
    }
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {parameters.map((param, index) => {
          const Icon = param.icon;
          return (
            <Card key={index} className="border-border/50 shadow-elegant">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-muted-foreground">{param.name}</h4>
                  <Icon className={`w-4 h-4 ${param.status === 'normal' ? 'text-success' : 'text-warning'}`} />
                </div>
                <div className="space-y-1">
                  <p className="text-2xl font-bold text-foreground">{param.value}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">Tolerance: {param.tolerance}</span>
                    <Badge variant={param.status === 'normal' ? 'default' : 'secondary'} 
                           className={param.status === 'normal' ? 'bg-success/10 text-success border-success/20' : 'bg-warning/10 text-warning border-warning/20'}>
                      {param.status === 'normal' ? 'PASS' : 'WATCH'}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card className="border-border/50 shadow-elegant">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              <span>Real-Time Track Geometry Analysis (EN 13848 Compliant)</span>
            </CardTitle>
            <Badge className="bg-primary/10 text-primary border-primary/20">
              Live Data • 25cm Sampling
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={geometryData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis 
                  dataKey="chainage" 
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  label={{ value: 'Chainage (KM)', position: 'insideBottom', offset: -10 }}
                />
                <YAxis 
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  label={{ value: 'Deviation (mm)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px'
                  }}
                />
                <Line type="monotone" dataKey="alignment" stroke="hsl(var(--primary))" strokeWidth={2} name="Alignment" />
                <Line type="monotone" dataKey="unevenness" stroke="hsl(var(--secondary))" strokeWidth={2} name="Unevenness" />
                <Line type="monotone" dataKey="twist" stroke="hsl(var(--accent))" strokeWidth={2} name="Twist" />
                <Line type="monotone" dataKey="crossLevel" stroke="hsl(var(--warning))" strokeWidth={2} name="Cross Level" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 text-sm text-muted-foreground">
            <p>Current section showing normal geometry parameters within EN 13848 Part 2 tolerance limits. 
            Cross level requires monitoring due to approaching threshold values.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}