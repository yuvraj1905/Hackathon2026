export interface SubTask {
  id: string;
  name: string;
  frontend: number;
  backend: number;
  integration?: number;
  testing: number;
  total: number;
  complexity?: string;
  children?: SubTask[];
}

export interface Module {
  id: string;
  name: string;
  expanded: boolean;
  tasks: SubTask[];
}
