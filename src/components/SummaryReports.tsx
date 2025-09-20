import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FileSpreadsheet, FileCode, Camera, Video } from "lucide-react";
import { exportToCSV, exportToXML, exportScreenshot, exportVideo, ExportData } from "@/utils/exportUtils";
import { toast } from "@/components/ui/use-toast";

export default function SummaryReports() {
  const lipFlowData = [
    { threshold: 1, leftRail: 16.75, rightRail: 5.75 },
    { threshold: 2, leftRail: 16.75, rightRail: 5.75 },
    { threshold: 3, leftRail: 0, rightRail: 0 },
    { threshold: 4, leftRail: 0, rightRail: 0 },
    { threshold: 5, leftRail: 0, rightRail: 0 }
  ];

  const verticalWearData = [
    { threshold: 8, leftRail: 29.75, rightRail: 11.5 },
    { threshold: 9, leftRail: 29.75, rightRail: 11.5 },
    { threshold: 10, leftRail: 29.75, rightRail: 11.5 },
    { threshold: 11, leftRail: 29.75, rightRail: 11.5 },
    { threshold: 12, leftRail: 29.75, rightRail: 11.5 },
    { threshold: 13, leftRail: 29.75, rightRail: 11.5 },
    { threshold: 14, leftRail: 27, rightRail: 5.5 },
    { threshold: 15, leftRail: 9.75, rightRail: 5.5 }
  ];

  const handleExport = (format: 'csv' | 'xml' | 'jpeg' | 'avi', reportType: 'lipflow' | 'verticalwear') => {
    const data = reportType === 'lipflow' ? lipFlowData : verticalWearData;
    const exportData: ExportData = {
      headers: [
        reportType === 'lipflow' ? 'Threshold of lip flow (mm)' : 'Threshold of Vertical wear (mm)',
        'Total length of track exceeding threshold in Left rail(m)',
        'Total length of track exceeding threshold in Right rail(m)'
      ],
      data: data.map(row => [
        row.threshold,
        row.leftRail,
        row.rightRail
      ]),
      filename: `${reportType}_summary_report`
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
          exportScreenshot(`${reportType}-report-table`, exportData.filename);
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

  const ExportButtons = ({ reportType }: { reportType: 'lipflow' | 'verticalwear' }) => (
    <div className="flex flex-wrap gap-2 justify-center mb-4">
      <Button 
        onClick={() => handleExport('csv', reportType)}
        variant="outline" 
        size="sm"
        className="flex items-center space-x-2"
      >
        <FileSpreadsheet className="w-4 h-4" />
        <span>CSV</span>
      </Button>
      <Button 
        onClick={() => handleExport('xml', reportType)}
        variant="outline" 
        size="sm"
        className="flex items-center space-x-2"
      >
        <FileCode className="w-4 h-4" />
        <span>XML</span>
      </Button>
      <Button 
        onClick={() => handleExport('jpeg', reportType)}
        variant="outline" 
        size="sm"
        className="flex items-center space-x-2"
      >
        <Camera className="w-4 h-4" />
        <span>JPEG</span>
      </Button>
      <Button 
        onClick={() => handleExport('avi', reportType)}
        variant="outline" 
        size="sm"
        className="flex items-center space-x-2"
      >
        <Video className="w-4 h-4" />
        <span>AVI</span>
      </Button>
    </div>
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Lip Flow Report */}
      <Card className="border-border/50 shadow-elegant">
        <CardHeader>
          <div className="text-center space-y-2">
            <CardTitle className="text-lg font-bold text-primary">
              East Coast Railway / Khurda Road
            </CardTitle>
            <div className="text-sm text-muted-foreground space-y-1">
              <p>Section: Barang-Khurda Road Line: UP Line KM : 420 to 450</p>
              <p>TRC No. :8001 - RUN Date :19-Mar-2025 - RUN No. :19-03-2025/b</p>
            </div>
            <Badge className="bg-primary/10 text-primary border-primary/20">
              Reporting Date: 17/09/2025 13:52:40
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <ExportButtons reportType="lipflow" />
          <div id="lipflow-report-table">
            <h3 className="text-center font-semibold mb-4 text-foreground">
              Summary report for Lip Flow
            </h3>
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead className="text-center font-semibold">
                    Threshold of lip flow (mm)
                  </TableHead>
                  <TableHead className="text-center font-semibold">
                    Total length of track exceeding threshold in Left rail(m)
                  </TableHead>
                  <TableHead className="text-center font-semibold">
                    Total length of track exceeding threshold in Right rail(m)
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {lipFlowData.map((row) => (
                  <TableRow key={row.threshold} className="hover:bg-muted/20">
                    <TableCell className="text-center">{row.threshold}</TableCell>
                    <TableCell className="text-center text-primary font-medium">
                      {row.leftRail}
                    </TableCell>
                    <TableCell className="text-center text-primary font-medium">
                      {row.rightRail}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Vertical Wear Report */}
      <Card className="border-border/50 shadow-elegant">
        <CardHeader>
          <div className="text-center space-y-2">
            <CardTitle className="text-lg font-bold text-primary">
              East Coast Railway / Khurda Road
            </CardTitle>
            <div className="text-sm text-muted-foreground space-y-1">
              <p>Section: Barang-Khurda Road Line: UP Line KM : 420 to 450</p>
              <p>TRC No. :8001 - RUN Date :19-Mar-2025 - RUN No. :19-03-2025/b</p>
            </div>
            <Badge className="bg-primary/10 text-primary border-primary/20">
              Reporting Date: 17/09/2025 13:53:17
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <ExportButtons reportType="verticalwear" />
          <div id="verticalwear-report-table">
            <h3 className="text-center font-semibold mb-4 text-foreground">
              Summary report for Vertical Wear
            </h3>
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead className="text-center font-semibold">
                    Threshold of Vertical wear (mm)
                  </TableHead>
                  <TableHead className="text-center font-semibold">
                    Total length of track exceeding threshold in Left rail(m)
                  </TableHead>
                  <TableHead className="text-center font-semibold">
                    Total length of track exceeding threshold in Right rail(m)
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {verticalWearData.map((row) => (
                  <TableRow key={row.threshold} className="hover:bg-muted/20">
                    <TableCell className="text-center">{row.threshold}</TableCell>
                    <TableCell className="text-center text-primary font-medium">
                      {row.leftRail}
                    </TableCell>
                    <TableCell className="text-center text-primary font-medium">
                      {row.rightRail}
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