import { Activity, Settings, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import tracsLogo from "@/assets/tracs-logo.png";

export default function SystemHeader() {
  return (
    <header className="bg-gradient-primary border-b border-border/50 shadow-elegant">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              <div className="bg-white rounded-full p-1 flex items-center justify-center w-10 h-10">
                <img src={tracsLogo} alt="TRACS Logo" className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-primary-foreground">TRACS</h1>
                <p className="text-sm text-primary-foreground/80">Track Reliability and Condition Surveillance</p>
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
            <Button variant="header" size="sm">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
            <Button variant="header" size="sm">
              <User className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}