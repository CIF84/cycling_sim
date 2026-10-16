import { ModelError, message } from "./messages";
import { demoRoute, parseGPX } from "./route";
import { simulate, compare } from "./physics";
import type { Inputs, Route } from "./types";
export interface Request {
  id: number;
  inputs: Inputs;
  route?: Route;
  xml?: string;
  name?: string;
  smoothingM?: number;
}
self.onmessage = (event: MessageEvent<Request>) => {
  const { id, inputs, xml, name, smoothingM } = event.data;
  try {
    const route =
      xml !== undefined
        ? parseGPX(xml, name, smoothingM)
        : (event.data.route ?? demoRoute());
    const ride = simulate(route, inputs);
    self.postMessage({
      id,
      route,
      ride,
      comparisons: compare(route, inputs, ride),
    });
  } catch (error) {
    self.postMessage({
      id,
      error:
        error instanceof ModelError
          ? error.detail
          : message("Unable to process this route."),
    });
  }
};
