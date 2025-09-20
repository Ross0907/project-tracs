import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Shield, Zap, Eye, Award } from "lucide-react";
import heroImage from "@/assets/hero-image.jpg";

export default function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-gradient-primary text-primary-foreground">
      <div className="absolute inset-0">
        <img 
          src={heroImage} 
          alt="Advanced railway monitoring technology with high-speed train and sensor systems"
          className="w-full h-full object-cover opacity-20"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-primary/80 to-primary/60" />
      </div>
      
      <div className="relative container mx-auto px-6 py-16">
        <div className="max-w-4xl">
          <div className="flex items-center space-x-3 mb-6">
            <Badge className="bg-secondary text-secondary-foreground">
              SIH 2025 Project
            </Badge>
            <Badge className="bg-primary-foreground/20 text-primary-foreground border-primary-foreground/30">
              Indigenous Technology
            </Badge>
          </div>
          
          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            Indigenous Track 
            <span className="bg-gradient-secondary bg-clip-text text-transparent"> Monitoring System</span>
          </h1>
          
          <p className="text-xl md:text-2xl mb-8 text-primary-foreground/90 leading-relaxed">
            Advanced contactless monitoring solution for Indian Railways featuring AI-powered defect detection, 
            real-time track geometry analysis, and comprehensive compliance with EN 13848 & RDSO standards.
          </p>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
            <div className="text-center">
              <div className="bg-primary-foreground/10 rounded-full p-4 w-16 h-16 mx-auto mb-3 flex items-center justify-center">
                <Zap className="w-8 h-8 text-secondary" />
              </div>
              <p className="text-sm font-medium">Real-time Processing</p>
            </div>
            <div className="text-center">
              <div className="bg-primary-foreground/10 rounded-full p-4 w-16 h-16 mx-auto mb-3 flex items-center justify-center">
                <Eye className="w-8 h-8 text-secondary" />
              </div>
              <p className="text-sm font-medium">AI Defect Detection</p>
            </div>
            <div className="text-center">
              <div className="bg-primary-foreground/10 rounded-full p-4 w-16 h-16 mx-auto mb-3 flex items-center justify-center">
                <Shield className="w-8 h-8 text-secondary" />
              </div>
              <p className="text-sm font-medium">Standards Compliant</p>
            </div>
            <div className="text-center">
              <div className="bg-primary-foreground/10 rounded-full p-4 w-16 h-16 mx-auto mb-3 flex items-center justify-center">
                <Award className="w-8 h-8 text-secondary" />
              </div>
              <p className="text-sm font-medium">Indigenous Solution</p>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4">
            <Button variant="secondary" size="lg" className="shadow-elegant" asChild>
              <a
                href={(import.meta as any).env?.VITE_POC_URL || "http://127.0.0.1:5050/"}
                target="_blank"
                rel="noopener noreferrer"
                title="Open Live Dashboard (Python POC)"
              >
                <Shield className="w-5 h-5 mr-2" />
                View Live Dashboard
              </a>
            </Button>
            <Button variant="header" size="lg" asChild>
              <a
                href="https://docs.google.com/presentation/d/10o0g5m8tqTOrJl_9YQ87jeHeqtqsHYpaaKF-_CRO-ag/edit?usp=sharing"
                target="_blank"
                rel="noopener noreferrer"
                title="Open Technical Documentation (Google Slides)"
              >
                <Award className="w-5 h-5 mr-2" />
                Technical Documentation
              </a>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}