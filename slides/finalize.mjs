import path from 'node:path';
import fs from 'node:fs/promises';
import {pathToFileURL,fileURLToPath} from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const skill=process.env.PRESENTATIONS_SKILL_DIR;
const python=process.env.RUNTIME_PYTHON;
if(!skill||!python)throw Error('Set PRESENTATIONS_SKILL_DIR and RUNTIME_PYTHON');
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const finalPath=process.env.SLIDES_FINAL_PATH || path.join(root,'tmp/slides-final/Slides-Redes-revisados.pptx');
await fs.mkdir(path.dirname(finalPath),{recursive:true});
const result=await finalizePresentation({
 workspaceDir:root,candidatePath:path.join(root,'tmp/slides-build/candidate.pptx'),finalPath,
 explicitTotalSlideCount:14,requiredNativeTableOwnerSlides:[4,8,9,12],requiredNativeChartOwnerSlides:[10,11,13],
 materializeLiteralChartWorkbooks:true,
 pythonExecutable:python,
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',
  ...[4,8,9,12].flatMap(n=>['--require-native-table-slide',String(n)])],
 fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,
 receiptPath:path.join(root,'tmp/slides-build',path.basename(finalPath)+'.validation.json')
});
console.log(JSON.stringify(result));
