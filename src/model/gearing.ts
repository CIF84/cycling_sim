import type { Inputs } from "./types";

// Curated examples, not a claim that every bike with this groupset has this gearing.
// Every tooth count is transcribed from manufacturer data: see docs/GROUPSETS.md.
export const GEARING_CHECKED_ON = "2026-10-16";
export type GroupsetCategory =
  | "shimano-road"
  | "shimano-gravel"
  | "shimano-cues"
  | "sram-road"
  | "sram-gravel";
export interface PartReference {
  readonly model: string;
  readonly url: string;
}
export interface Cassette extends PartReference {
  readonly cogs: readonly number[];
}
export interface GroupsetPreset {
  readonly id: string;
  readonly name: string;
  readonly category: GroupsetCategory;
  readonly chainrings: readonly number[];
  readonly crank: PartReference;
  readonly cassette: Cassette;
  readonly derailleur: PartReference;
}

const shimanoProduct = (model: string): PartReference => ({
  model,
  url: `https://bike.shimano.com/en-NA/products/components/pdp.P-${model}.html`,
});
const sramProduct = (model: string): PartReference => ({
  model,
  url: `https://www.sram.com/en/service/models/${model.toLowerCase()}`,
});
const shimanoCompatibility =
  "https://productinfo.shimano.com/en/compatibility/C-254";
const shimanoRoadManual =
  "https://si.shimano.com/en/pdfs/dm/RACS010/DM-RACS010-04-ENG.pdf";
const shimanoXtDiagram =
  "https://si.shimano.com/en/pdfs/ev/CS-M8100-4507/EV-CS-M8100-4507B.pdf";
const shimanoCues =
  "https://bike.shimano.com/en-UK/stories/article/shimano-cues-for-drop-bar.html";
const cassette = (
  model: string,
  cogs: readonly number[],
  url: string,
): Cassette => ({ model, cogs, url });

const cassettes = {
  duraAce: cassette(
    "CS-R9200-12",
    [11, 12, 13, 14, 15, 16, 17, 19, 21, 24, 27, 30],
    "https://si.shimano.com/en/pdfs/ev/CS-R9200-4808/EV-CS-R9200-4808.pdf",
  ),
  ultegra: cassette(
    "CS-R8100-12",
    [11, 12, 13, 14, 15, 17, 19, 21, 24, 27, 30, 34],
    shimanoRoadManual,
  ),
  road105: cassette(
    "CS-R7101-12",
    [11, 12, 13, 14, 15, 17, 19, 21, 24, 27, 30, 34],
    shimanoRoadManual,
  ),
  tiagra: cassette(
    "CS-RS400-11",
    [11, 13, 15, 17, 19, 21, 23, 25, 28, 32, 36],
    "https://si.shimano.com/en/pdfs/dm/LACS001/DM-LACS001-02-ENG.pdf",
  ),
  sora: cassette(
    "CS-HG400-9",
    [11, 12, 14, 16, 18, 21, 24, 28, 32],
    "https://si.shimano.com/en/pdfs/dm/CS0003/DM-CS0003-08-ENG.pdf",
  ),
  claris: cassette(
    "CS-HG50-8",
    [11, 13, 15, 18, 21, 24, 28, 32],
    "https://si.shimano.com/en/pdfs/ev/CS-HG50-8-3072/EV-CS-HG50-8-3072C.pdf",
  ),
  gravelDouble: cassette(
    "CS-HG710-12",
    [11, 12, 13, 14, 15, 17, 19, 21, 24, 28, 32, 36],
    shimanoRoadManual,
  ),
  gravelClose: cassette(
    "CS-M8100-12",
    [10, 12, 14, 16, 18, 21, 24, 28, 32, 36, 40, 45],
    shimanoXtDiagram,
  ),
  gravelWide: cassette(
    "CS-M8100-12",
    [10, 12, 14, 16, 18, 21, 24, 28, 33, 39, 45, 51],
    shimanoXtDiagram,
  ),
  gravel10: cassette(
    "CS-HG500-10",
    [11, 13, 15, 17, 19, 21, 23, 26, 30, 34],
    "https://si.shimano.com/en/pdfs/ev/CS-HG500-10-3861/EV-CS-HG500-10-3861A.pdf",
  ),
  cues: cassette(
    "CS-LG400-11",
    [11, 13, 15, 17, 20, 23, 26, 30, 36, 43, 50],
    "https://si.shimano.com/en/pdfs/ev/CS-LG700-11-4937/EV-CS-LG700-11-4937.pdf",
  ),
  red: cassette(
    "CS-XG-1290-E1",
    [10, 11, 12, 13, 14, 15, 17, 19, 21, 24, 28, 33],
    sramProduct("CS-XG-1290-E1").url,
  ),
  force: cassette(
    "CS-XG-1270-E1",
    [10, 11, 12, 13, 15, 17, 19, 21, 24, 28, 32, 36],
    sramProduct("CS-XG-1270-E1").url,
  ),
  rival: cassette(
    "CS-XG-1250-D1",
    [10, 11, 12, 13, 15, 17, 19, 21, 24, 28, 32, 36],
    sramProduct("CS-XG-1250-D1").url,
  ),
  redXplr: cassette(
    "CS-XG-1391-E1",
    [10, 11, 12, 13, 15, 17, 19, 21, 24, 28, 32, 38, 46],
    sramProduct("CS-XG-1391-E1").url,
  ),
  forceXplr: cassette(
    "CS-XG-1371-E1",
    [10, 11, 12, 13, 15, 17, 19, 21, 24, 28, 32, 38, 46],
    sramProduct("CS-XG-1371-E1").url,
  ),
  rivalXplr: cassette(
    "CS-XG-1351-E1",
    [10, 11, 12, 13, 15, 17, 19, 21, 24, 28, 32, 38, 46],
    sramProduct("CS-XG-1351-E1").url,
  ),
  apex: cassette(
    "CS-PG-1231-D1",
    [11, 12, 13, 15, 17, 19, 21, 24, 28, 32, 38, 44],
    sramProduct("CS-PG-1231-D1").url,
  ),
} as const;

function shimano(
  id: string,
  name: string,
  category: GroupsetCategory,
  chainrings: readonly number[],
  crank: string,
  cassetteKey: keyof typeof cassettes,
  derailleur: string,
): GroupsetPreset {
  return {
    id,
    name,
    category,
    chainrings,
    crank: shimanoProduct(crank),
    cassette: cassettes[cassetteKey],
    derailleur: {
      model: derailleur,
      url: category === "shimano-cues" ? shimanoCues : shimanoCompatibility,
    },
  };
}
function sram(
  id: string,
  name: string,
  category: GroupsetCategory,
  chainrings: readonly number[],
  crank: string,
  cassetteKey: keyof typeof cassettes,
  derailleur: string,
): GroupsetPreset {
  return {
    id,
    name,
    category,
    chainrings,
    crank: sramProduct(crank),
    cassette: cassettes[cassetteKey],
    derailleur: sramProduct(derailleur),
  };
}

export const GROUPSET_PRESETS: readonly GroupsetPreset[] = [
  shimano(
    "shimano-dura-ace-r9200",
    "DURA-ACE R9200 Di2",
    "shimano-road",
    [36, 52],
    "FC-R9200",
    "duraAce",
    "RD-R9250",
  ),
  shimano(
    "shimano-ultegra-r8100",
    "ULTEGRA R8100 Di2",
    "shimano-road",
    [34, 50],
    "FC-R8100",
    "ultegra",
    "RD-R8150",
  ),
  shimano(
    "shimano-105-r7100",
    "105 R7100 / Di2",
    "shimano-road",
    [34, 50],
    "FC-R7100",
    "road105",
    "RD-R7100 / RD-R7150",
  ),
  shimano(
    "shimano-tiagra-r4000",
    "TIAGRA R4000",
    "shimano-road",
    [34, 50],
    "FC-R4000",
    "tiagra",
    "RD-R4000",
  ),
  shimano(
    "shimano-sora-r3000",
    "SORA R3000",
    "shimano-road",
    [34, 50],
    "FC-R3000",
    "sora",
    "RD-R3000-GS",
  ),
  shimano(
    "shimano-claris-r2000",
    "CLARIS R2000",
    "shimano-road",
    [34, 50],
    "FC-R2000",
    "claris",
    "RD-R2000-GS",
  ),
  shimano(
    "shimano-grx-rx825",
    "GRX RX825 Di2",
    "shimano-gravel",
    [31, 48],
    "FC-RX820-2",
    "gravelDouble",
    "RD-RX825",
  ),
  shimano(
    "shimano-grx-rx827",
    "GRX RX827 Di2",
    "shimano-gravel",
    [40],
    "FC-RX820-1",
    "gravelWide",
    "RD-RX827-SGS",
  ),
  shimano(
    "shimano-grx-rx717",
    "GRX RX717 Di2",
    "shimano-gravel",
    [40],
    "FC-RX610-1",
    "gravelWide",
    "RD-RX717-SGS",
  ),
  shimano(
    "shimano-grx-rx820-2x",
    "GRX RX820 · 2×12",
    "shimano-gravel",
    [31, 48],
    "FC-RX820-2",
    "gravelDouble",
    "RD-RX820",
  ),
  shimano(
    "shimano-grx-rx820-1x45",
    "GRX RX820 · 1×12 · 10–45",
    "shimano-gravel",
    [40],
    "FC-RX820-1",
    "gravelClose",
    "RD-RX822-GS",
  ),
  shimano(
    "shimano-grx-rx820-1x51",
    "GRX RX820 · 1×12 · 10–51",
    "shimano-gravel",
    [40],
    "FC-RX820-1",
    "gravelWide",
    "RD-RX822-SGS",
  ),
  shimano(
    "shimano-grx-rx610-2x",
    "GRX RX610 · 2×12",
    "shimano-gravel",
    [30, 46],
    "FC-RX610-2",
    "gravelDouble",
    "RD-RX820",
  ),
  shimano(
    "shimano-grx-rx610-1x",
    "GRX RX610 · 1×12",
    "shimano-gravel",
    [40],
    "FC-RX610-1",
    "gravelWide",
    "RD-RX822-SGS",
  ),
  shimano(
    "shimano-grx-rx400",
    "GRX RX400 · 2×10",
    "shimano-gravel",
    [30, 46],
    "FC-RX600-10",
    "gravel10",
    "RD-RX400",
  ),
  shimano(
    "shimano-cues-2x",
    "CUES U6040 · 2×11",
    "shimano-cues",
    [32, 46],
    "FC-U6040-2",
    "tiagra",
    "RD-U6040",
  ),
  shimano(
    "shimano-cues-1x",
    "CUES U6000 · 1×11",
    "shimano-cues",
    [40],
    "FC-U6030-1",
    "cues",
    "RD-U6000",
  ),
  sram(
    "sram-red-axs-e1",
    "RED AXS E1",
    "sram-road",
    [35, 48],
    "FC-RED-E1",
    "red",
    "RD-RED-E-E1",
  ),
  sram(
    "sram-force-axs-e1",
    "Force AXS E1",
    "sram-road",
    [35, 48],
    "FC-FRC-E1",
    "force",
    "RD-FRC-E-E1",
  ),
  sram(
    "sram-rival-axs-e1",
    "Rival AXS E1",
    "sram-road",
    [33, 46],
    "FC-RIV-E1",
    "rival",
    "RD-RIV-E-E1",
  ),
  sram(
    "sram-red-xplr-e1",
    "RED XPLR AXS E1",
    "sram-gravel",
    [42],
    "FC-RED-1W-E1",
    "redXplr",
    "RD-RED-1E-E1",
  ),
  sram(
    "sram-force-xplr-e1",
    "Force XPLR AXS E1",
    "sram-gravel",
    [42],
    "FC-FRC-1W-E1",
    "forceXplr",
    "RD-FRC-1E-E1",
  ),
  sram(
    "sram-rival-xplr-e1",
    "Rival XPLR AXS E1",
    "sram-gravel",
    [40],
    "FC-RIV-1W-E1",
    "rivalXplr",
    "RD-RIV-1E-E1",
  ),
  sram(
    "sram-apex-xplr-axs",
    "Apex XPLR AXS D1",
    "sram-gravel",
    [40],
    "FC-APX-1W-D1",
    "apex",
    "RD-APX-1E-D1",
  ),
  sram(
    "sram-apex-xplr",
    "Apex XPLR D1",
    "sram-gravel",
    [40],
    "FC-APX-1W-D1",
    "apex",
    "RD-APX-1-D1",
  ),
];

export const DEFAULT_GROUPSET_ID = "shimano-105-r7100";
export const DEFAULT_GROUPSET = GROUPSET_PRESETS.find(
  (p) => p.id === DEFAULT_GROUPSET_ID,
)!;

// A gear choice must never silently change power, mass, efficiency, tires or wheel size.
// Fresh arrays also protect the reference catalog from manual input edits.
export function applyGroupset(inputs: Inputs, preset: GroupsetPreset): Inputs {
  return {
    ...inputs,
    chainrings: [...preset.chainrings],
    cogs: [...preset.cassette.cogs],
  };
}

export function sameTeeth(a: readonly number[], b: readonly number[]): boolean {
  const sortedB = [...b].sort((x, y) => x - y);
  return (
    a.length === b.length &&
    [...a].sort((x, y) => x - y).every((n, i) => n === sortedB[i])
  );
}
