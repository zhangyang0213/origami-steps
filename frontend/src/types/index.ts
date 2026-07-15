// 折纸步骤数据
export interface StepData {
  step_number: number;
  title: string;
  image_url: string;
  description: string;
}

// 教程结果
export interface TutorialResult {
  title: string;
  source_url: string;
  steps: StepData[];
}

// 搜索响应
export interface SearchResponse {
  query: string;
  results: TutorialResult[];
}
