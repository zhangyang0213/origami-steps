export interface StepData {
  step_number: number;
  title: string;
  image_url: string;
  description: string;
}

export interface TutorialResult {
  title: string;
  source_url: string;
  steps: StepData[];
}

export interface SearchResponse {
  query: string;
  results: TutorialResult[];
  error: string;
  is_demo: boolean;
}
