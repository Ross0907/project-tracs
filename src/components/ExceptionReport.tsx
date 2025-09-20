import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Download, FileSpreadsheet, FileCode, Camera, Video } from "lucide-react";
import { exportToCSV, exportToXML, exportScreenshot, exportVideo, ExportData } from "@/utils/exportUtils";
import { toast } from "@/components/ui/use-toast";

export default function ExceptionReport() {
  const reportData = [
    {
      sno: 1,
      timeOfDetection: "Wed Mar 19 12:15:32 IST 2025",
      side: "Left",
      locationKm: 420,
      locationMeter: 33.94,
      sizeL: 240,
      sizeB: 322,
      sizeH: 467,
      distanceFromCenter: 2153,
      heightFromRail: 1175,
      sodEnvelope: "SOD-In station"
    },
    {
      sno: 2,
      timeOfDetection: "Wed Mar 19 12:15:32 IST 2025",
      side: "Left",
      locationKm: 420,
      locationMeter: 33.94,
      sizeL: 120,
      sizeB: 322,
      sizeH: 467,
      distanceFromCenter: 2153,
      heightFromRail: 1175,
      sodEnvelope: "SOD-In station"
    },
    {
      sno: 3,
      timeOfDetection: "Wed Mar 19 12:15:40 IST 2025",
      side: "Left",
      locationKm: 420,
      locationMeter: 136.26,
      sizeL: 1080,
      sizeB: 518,
      sizeH: 61,
      distanceFromCenter: 731,
      heightFromRail: 151,
      sodEnvelope: "MND"
    },
    {
      sno: 4,
      timeOfDetection: "Wed Mar 19 12:15:44 IST 2025",
      side: "Right",
      locationKm: 420,
      locationMeter: 175.02,
      sizeL: 240,
      sizeB: 137,
      sizeH: 2872,
      distanceFromCenter: 2234,
      heightFromRail: 3614,
      sodEnvelope: "SOD-Out station"
    },
    {
      sno: 5,
      timeOfDetection: "Wed Mar 19 12:15:44 IST 2025",
      side: "Right",
      locationKm: 420,
      locationMeter: 175.02,
      sizeL: 240,
      sizeB: 138,
      sizeH: 3237,
      distanceFromCenter: 2234,
      heightFromRail: 3614,
      sodEnvelope: "SOD-In station"
    }
  ];

  const handleExport = (format: 'csv' | 'xml' | 'jpeg' | 'avi') => {
    const exportData: ExportData = {
      headers: [
        'S.No', 'Time Of Detection', 'Side', 'Location Km', 'Location Meter',
        'Size L (mm)', 'Size B (mm)', 'Size H (mm)', 'Distance From Center Line',
        'Height From Rail Level', 'SOD Envelope'
      ],
      data: reportData.map(row => [
        row.sno,
        row.timeOfDetection,
        row.side,
        row.locationKm,
        row.locationMeter,
        row.sizeL,
        row.sizeB,
        row.sizeH,
        row.distanceFromCenter,
        row.heightFromRail,
        row.sodEnvelope
      ]),
      filename: 'exception_report_summary'
    };

    try {
      switch (format) {
        case 'csv':
          exportToCSV(exportData);
          toast({ title: 'Exported CSV', description: `${exportData.filename}.csv saved.` });
          break;
        case 'xml':
          exportToXML(exportData);
          toast({ title: 'Exported XML', description: `${exportData.filename}.xml saved.` });
          break;
        case 'jpeg':
          exportScreenshot('exception-report-table', exportData.filename);
          toast({ title: 'Exporting JPEG', description: `Saving ${exportData.filename}.jpg...` });
          break;
        case 'avi':
          exportVideo(exportData.filename);
          break;
      }
    } catch (err) {
      console.error('Export failed', err);
      toast({ title: 'Export failed', description: 'Please try again.', variant: 'destructive' });
    }
  };

  return (
    <div className="space-y-6">
      <Card className="border-border/50 shadow-elegant">
        <CardHeader>
          <div className="space-y-4">
            <div className="text-center">
              <CardTitle className="text-lg font-bold text-primary mb-2">
                EXCEPTION REPORT-SUMMARY OF INFRINGEMENTS IN SCHEDULE OF DIMENSIONS
              </CardTitle>
              <div className="text-sm text-muted-foreground space-y-1">
                <p>East Coast Railway / Khurda Road</p>
                <p>Section: Barang-Khurda Road Line: UP Line KM : 420 to 450</p>
                <p>TRC No. :8001 - RUN Date :19-Mar-2025 - RUN No. :19-03-2025/b</p>
                <p className="text-primary font-semibold">SOD Envelope - ALL</p>
              </div>
              <Badge className="bg-primary/10 text-primary border-primary/20 mt-2">
                Reporting Date: 17/09/2025 13:50:52
              </Badge>
            </div>
            
            <div className="flex flex-wrap gap-2 justify-center">
              <Button 
                onClick={() => handleExport('csv')}
                variant="outline" 
                size="sm"
                className="flex items-center space-x-2"
              >
                <FileSpreadsheet className="w-4 h-4" />
                <span>Export CSV</span>
              </Button>
              <Button 
                onClick={() => handleExport('xml')}
                variant="outline" 
                size="sm"
                className="flex items-center space-x-2"
              >
                <FileCode className="w-4 h-4" />
                <span>Export XML</span>
              </Button>
              <Button 
                onClick={() => handleExport('jpeg')}
                variant="outline" 
                size="sm"
                className="flex items-center space-x-2"
              >
                <Camera className="w-4 h-4" />
                <span>Export JPEG</span>
              </Button>
              <Button 
                onClick={() => handleExport('avi')}
                variant="outline" 
                size="sm"
                className="flex items-center space-x-2"
              >
                <Video className="w-4 h-4" />
                <span>Export AVI</span>
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div id="exception-report-table" className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead className="text-center font-semibold">S.No.</TableHead>
                  <TableHead className="text-center font-semibold">Time Of Detection</TableHead>
                  <TableHead className="text-center font-semibold">Side</TableHead>
                  <TableHead className="text-center font-semibold" colSpan={2}>Location</TableHead>
                  <TableHead className="text-center font-semibold" colSpan={3}>Size Of Obstacle (mm)</TableHead>
                  <TableHead className="text-center font-semibold">Distance From Centre Line Of Track(mm)</TableHead>
                  <TableHead className="text-center font-semibold">Height From Rail Level(mm)</TableHead>
                  <TableHead className="text-center font-semibold">SOD Envelope</TableHead>
                </TableRow>
                <TableRow className="bg-muted/30">
                  <TableHead></TableHead>
                  <TableHead></TableHead>
                  <TableHead></TableHead>
                  <TableHead className="text-center font-semibold">Km</TableHead>
                  <TableHead className="text-center font-semibold">Meter</TableHead>
                  <TableHead className="text-center font-semibold">L</TableHead>
                  <TableHead className="text-center font-semibold">B</TableHead>
                  <TableHead className="text-center font-semibold">H</TableHead>
                  <TableHead></TableHead>
                  <TableHead></TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reportData.map((row) => (
                  <TableRow key={row.sno} className="hover:bg-muted/20">
                    <TableCell className="text-center">{row.sno}</TableCell>
                    <TableCell className="text-sm">{row.timeOfDetection}</TableCell>
                    <TableCell className="text-center">{row.side}</TableCell>
                    <TableCell className="text-center">{row.locationKm}</TableCell>
                    <TableCell className="text-center">{row.locationMeter}</TableCell>
                    <TableCell className="text-center">{row.sizeL}</TableCell>
                    <TableCell className="text-center">{row.sizeB}</TableCell>
                    <TableCell className="text-center">{row.sizeH}</TableCell>
                    <TableCell className="text-center">{row.distanceFromCenter}</TableCell>
                    <TableCell className="text-center">{row.heightFromRail}</TableCell>
                    <TableCell className="text-center">
                      <Badge variant="outline" className="text-xs">
                        {row.sodEnvelope}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}