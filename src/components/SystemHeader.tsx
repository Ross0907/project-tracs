import { Activity, Monitor, Settings, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function SystemHeader() {
  return (
    <header className="bg-gradient-primary border-b border-border/50 shadow-elegant">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              <Monitor className="w-8 h-8 text-primary-foreground" />
              <div>
                <h1 className="text-2xl font-bold text-primary-foreground">ITMS</h1>
                <p className="text-sm text-primary-foreground/80">Indigenous Track Monitoring System</p>
              </div>
            </div>
            <Badge variant="secondary" className="ml-4">
              <Activity className="w-3 h-3 mr-1" />
              LIVE
            </Badge>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-right text-primary-foreground/90">
              <p className="text-sm font-medium">System Status: Online</p>
              <p className="text-xs">EN 13848 & RDSO Compliant</p>
            </div>
            <Button variant="outline" size="sm" className="border-primary-foreground/20 text-primary-foreground hover:bg-primary-foreground/10">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
            <Button variant="outline" size="sm" className="border-primary-foreground/20 text-primary-foreground hover:bg-primary-foreground/10">
              <User className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}