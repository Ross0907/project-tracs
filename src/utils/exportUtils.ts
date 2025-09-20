export interface ExportData {
  headers: string[];
  data: (string | number)[][];
  filename: string;
}

// CSV Export
export function exportToCSV(exportData: ExportData): void {
  const escapeCsv = (value: string | number) => {
    const s = String(value);
    // Escape double quotes by doubling them
    const escaped = s.replace(/"/g, '""');
    // Quote if contains comma, quote, or newline
    return /[",\n\r]/.test(escaped) ? `"${escaped}"` : escaped;
  };

  const lines = [
    exportData.headers.map(escapeCsv).join(','),
    ...exportData.data.map(row => row.map(escapeCsv).join(','))
  ];

  // Prepend BOM for Excel compatibility and use CRLF newlines (Windows friendly)
  const csvContent = `\uFEFF${lines.join('\r\n')}`;

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.href = url;
  link.download = `${exportData.filename}.csv`;
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

// XML Export
export function exportToXML(exportData: ExportData): void {
  const escapeXml = (value: string | number) =>
    String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;');

  let xmlContent = '<?xml version="1.0" encoding="UTF-8"?>\n<report>\n';

  exportData.data.forEach((row) => {
    xmlContent += '  <record>\n';
    exportData.headers.forEach((header, headerIndex) => {
      const sanitizedHeader = header.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
      xmlContent += `    <${sanitizedHeader}>${escapeXml(row[headerIndex] ?? '')}</${sanitizedHeader}>\n`;
    });
    xmlContent += '  </record>\n';
  });

  xmlContent += '</report>';

  const blob = new Blob([xmlContent], { type: 'application/xml;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.href = url;
  link.download = `${exportData.filename}.xml`;
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

// Screenshot Export (JPEG)
import html2canvas from 'html2canvas';

export function exportScreenshot(elementId: string, filename: string): void {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(`exportScreenshot: element #${elementId} not found`);
    return;
  }

  html2canvas(element, {
    backgroundColor: '#ffffff',
    scale: window.devicePixelRatio && window.devicePixelRatio > 1 ? 2 : 1,
    logging: false,
    useCORS: true
  })
    .then((canvas) => {
      const link = document.createElement('a');
      link.download = `${filename}.jpg`;
      link.href = canvas.toDataURL('image/jpeg', 0.92);
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    })
    .catch((err) => {
      console.error('Screenshot export failed', err);
    });
}

// Video Export placeholder (AVI) - Would require actual video recording implementation
export function exportVideo(filename: string): void {
  // This would require implementing screen recording functionality
  // For now, we'll show a notification that this feature is coming soon
  alert('Video export (AVI) functionality coming soon. This would require screen recording implementation.');
}