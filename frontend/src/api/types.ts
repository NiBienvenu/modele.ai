// JSON shapes of the REST API. Must match api/schemas.py in the backend.

export type JobStatus = "pending" | "processing" | "completed" | "failed";

/** Answer of POST /question */
export interface QuestionAccepted {
  request_id: string;
  status: JobStatus;
}

/** Answer of GET /response/{request_id} */
export interface ResponseOut {
  request_id: string;
  status: JobStatus;
  response: string | null;
  tokens: number | null;
  elapsed_time: number | null;
  error: string | null;
}

export const isFinished = (status: JobStatus): boolean =>
  status === "completed" || status === "failed";
