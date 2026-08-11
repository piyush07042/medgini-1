import api from "./client";

export const getReportHtmlUrl = (patientId: number, template = "report_template.html") => {
  const query = template ? `?template=${encodeURIComponent(template)}` : "";
  return `/reports/${patientId}/html${query}`;
};

export const getReportPdfUrl = (patientId: number) => `/reports/${patientId}/pdf`;
export const getReportPdfDownloadUrl = (patientId: number) => `/reports/medigenie/${patientId}/pdf`;

export type ReportTemplateResponse = {
  templates: string[];
};

export const listReportTemplates = async (): Promise<ReportTemplateResponse> => {
  const response = await api.get<ReportTemplateResponse>("/reports/templates");
  return response.data;
};
