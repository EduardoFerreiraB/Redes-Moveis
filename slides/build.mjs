import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.dirname(here);
const out=process.env.SLIDES_BUILD_DIR || path.join(root,'tmp','slides-build');
await fs.mkdir(out,{recursive:true});
const data=JSON.parse(await fs.readFile(path.join(here,'dados.json'),'utf8'));
const deck=Presentation.create({slideSize:{width:1280,height:720}});
const bg='#0F1B2B',fg='#E9EFF4',muted='#B4C3CE',cyan='#50D3E1',font='Arial';
const colors=['#2878D0','#EB6834','#16A878'];
const protocols=['AODV','OLSR','DSDV'];
const speeds=[1,5,10,20];
const chartErrors=[];
function row(a,p,v){const r=data.find(r=>+r.area===a&&r.protocol===p&&+r.speed===v);if(!r)throw Error('Missing scenario');return r;}
function fmt(n,d=1){return Number(n).toFixed(d).replace('.',',');}
function text(s,t,x,y,w,h,size=28,color=fg,bold=false){
 const sh=s.shapes.add({geometry:'textbox',name:t.slice(0,50),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 sh.text=t;sh.text.style={fontFamily:font,fontSize:size,color,bold,insets:0,wrap:'word'};return sh;
}
function slide(title,notes=''){
 const s=deck.slides.add();s.background.fill=bg;
 text(s,title,80,55,1120,80,43,fg,true);
 text(s,String(deck.slides.items.length).padStart(2,'0'),1180,675,45,25,17,muted);
 s.speakerNotes.text=notes;return s;
}
function lines(s,items,y=185,size=29,gap=85){items.forEach((t,i)=>text(s,t,85,y+i*gap,1100,gap-10,size));}
function table(s,values,{x=80,y=160,w=1120,h=390,widths,size=25}={}){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});
 t.borders.assign({fill:'#667889',width:1,style:'solid'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?'#DDE5EA':bg;
  cell.text.style={fontFamily:font,fontSize:size,color:r===0?bg:fg,bold:r===0};
 }
 t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({margins:{left:14,right:14,top:10,bottom:8},anchor:'center'});
 return t;
}
function chart(s,area,metric,title,x,y,w,h,max,unit){
 const series=protocols.map((p,i)=>({name:p,xValues:speeds,values:speeds.map(v=>+row(area,p,v)[metric+'_mean']),
  line:{fill:colors[i],width:2.8,style:i===0?'solid':i===1?'dashed':'dotted'},
  marker:{symbol:['circle','square','triangle'][i],size:7,fill:colors[i]},fill:colors[i]}));
 const c=s.charts.add('scatter',{position:{left:x,top:y,width:w,height:h},title,titleTextStyle:{typeface:font,fontSize:25,fill:'#172536',bold:true},
  categories:speeds.map(String),series,scatterOptions:{style:'lineWithMarkers'},chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF',hasLegend:true,
  legend:{position:'bottom',overlay:false,textStyle:{typeface:font,fontSize:19,fill:'#172536'}},
  xAxis:{min:0,max:20,majorUnit:5,title:{text:'Velocidade (m/s)',textStyle:{typeface:font,fontSize:19,fill:'#172536'}},textStyle:{typeface:font,fontSize:18,fill:'#172536'},majorGridlines:{fill:'#DFE5EA',width:1},numberFormatCode:'0'},
  yAxis:{min:0,max,numberFormatCode:metric==='throughputMbps'?'0.00':'0',textStyle:{typeface:font,fontSize:18,fill:'#172536'},majorGridlines:{fill:'#DFE5EA',width:1},title:{text:unit,textStyle:{typeface:font,fontSize:19,fill:'#172536'}}}});
 chartErrors.push({index:chartErrors.length+1,ownerSlide:deck.slides.items.length,area,metric,series:protocols.map((p,i)=>({name:p,color:colors[i],ci:speeds.map(v=>+row(area,p,v)[metric+'_ci95'])}))});
 return c;
}

// 1. Reuse the original cover illustration, rendered from the supplied PDF.
{
 const s=deck.slides.add();s.background.fill=bg;
 text(s,'Redes Móveis · IFG Câmpus Inhumas · 2026/2',80,135,700,35,22,cyan);
 text(s,'Mobilidade e área\nem redes MANET',80,215,700,150,58,fg,true);
 text(s,'AODV, OLSR e DSDV com aproximação\nde perdas ambientais',80,390,680,95,30);
 text(s,'Eduardo Ferreira de Brito Matos\nPedro Américo Rocha e Thiago Ferreira\nProf. Rogério Sousa e Silva',80,545,720,110,24,muted);
 const bytes=await fs.readFile(path.join(here,'assets','rede-capa.png'));
 s.images.add({blob:bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),contentType:'image/png',alt:'Ilustração de rede da apresentação original',position:{left:770,top:110,width:450,height:476},fit:'contain'});
 s.speakerNotes.text='Fonte da ilustração: Slides Redes.pdf, versão anterior do grupo, página 1. Revisão metodológica de 17/11/2026, apresentação atualizada em 18/11/2026.';
}
// 2
{
 const s=slide('MANET e protocolos de roteamento','Fontes: RFC 3561 (https://www.rfc-editor.org/rfc/rfc3561), RFC 3626 (https://www.rfc-editor.org/rfc/rfc3626), Perkins e Bhagwat (1994), referências do artigo.');
 text(s,'Nós móveis comunicam-se sem infraestrutura fixa e encaminham pacotes por múltiplos saltos.',85,160,1100,95,30,cyan);
 protocols.forEach((p,i)=>{
  const x=85+i*390;text(s,p,x,310,340,55,39,colors[i],true);
  text(s,['Reativo','Proativo, estado de enlace','Proativo, vetor de distância'][i],x,380,340,65,26);
  text(s,['Descobre rotas quando há dados. Pacotes podem aguardar a descoberta em fila.','HELLO e TC mantêm a topologia. MPRs reduzem retransmissões de controle.','Tabelas de próximos saltos usam números de sequência para evitar rotas obsoletas.'][i],x,465,330,150,26,muted);
 });
}
// 3
{
 const s=slide('Objetivo e questão de pesquisa','Fonte: article/main.tex, introdução e metodologia. A variável adicional é a área. A velocidade continua como variável principal.');
 text(s,'Como a velocidade afeta a entrega e a latência\ndos protocolos de roteamento?',85,185,1100,125,39,cyan);
 text(s,'Essa tendência muda quando os mesmos 20 nós\nocupam áreas diferentes?',85,355,1100,125,39);
 text(s,'Métricas: PDR, vazão, atraso fim a fim e jitter',85,570,1100,60,28,muted);
}
// 4
{
 const s=slide('Cenário-base no ns-3.48','Fonte: src/manet-routing.cc e article/main.tex, Tabela 1. Ganhos TX/RX = 0 dB. A coordenada Z comum de 1,5 m não cria relevo. Commit ns-3: d2add90b452d600cfb4859baed8e9ea633519447.');
 table(s,[['Parâmetro','Configuração'],['Nós e área-base','20 nós em 500 × 500 m'],['Rádio','IEEE 802.11b ad hoc, DSSS a 11 Mb/s'],['Canal e potência','Canal 1, 2,412 GHz, 22 MHz, 16 dBm fixos'],['Propagação','Log-distance, expoente n = 2,7'],['Mobilidade','Random Waypoint, pausa zero, 1 / 5 / 10 / 20 m/s'],['Tráfego','4 fluxos UDP, 32768 bit/s por fluxo, 1024 bytes'],['Tempo','120 s, fontes por 90 s, início em [20,21) s']],{h:445,widths:[330,790],size:24});
 text(s,'Mesmos parâmetros do rádio e do ambiente em todas as áreas.',85,635,1120,45,25,cyan);
}
// 5
{
 const s=slide('Matriz experimental','Fonte: data/processed/area/validacao.json e comandos.txt de cada área. A comparação entre protocolos é pareada dentro da mesma área, velocidade, seed e run. Áreas diferentes não compartilham trajetórias físicas idênticas.');
 text(s,'3 áreas × 3 protocolos × 4 velocidades × 20 runs',85,205,1120,75,40);
 text(s,'720 simulações',85,320,1100,110,78,cyan,true);
 lines(s,['Seed fixa em 1 e runs de 1 a 20','Mesmas trajetórias entre protocolos na mesma configuração'],505,27,70);
}
// 6
{
 const s=slide('Rádio fixo e ajustes de implementação','Fontes: src/manet-routing.cc; docs/revisao-metodologica.md. O Friis anterior conservava o padrão 5,15 GHz. A faixa de 13–20 dBm é uma restrição informada pelo grupo, não um limite universal de 802.11b e não comprova hardware específico.');
 lines(s,['Potência constante de 16 dBm, sem adaptação durante as runs','Frequência de propagação coerente com o PHY: 2,412 GHz','Início das fontes em [20,21) s para reduzir sincronização ARP','ARP DeadTimeout = 1 s e FlowMonitor MaxPerHopDelay = 120 s'],170,28,100);
 text(s,'A revisão corrige a frequência implícita de 5,15 GHz do antigo Friis.',85,610,1110,60,25,cyan);
}
// 7
{
 const s=slide('Aproximação das perdas ambientais','Fontes: article/main.tex, seção 3.1; código ns-3.48 src/propagation/model/propagation-loss-model.cc. Documentação: https://www2.nsnam.org/docs/models/html/propagation.html. Para d <= 1 m o ns-3.48 mantém a perda em L0.');
 text(s,'L(d) = L₀ + 10 n log₁₀(d / d₀)',85,180,1120,75,46,cyan,true);
 text(s,'n = 2,7     d₀ = 1 m     L₀ = 40,0953 dB',85,280,1120,60,32);
 text(s,'Perda de referência calculada para 2,412 GHz\nO expoente representa atenuação média superior ao espaço livre.',85,380,1100,105,28);
 text(s,'Hipótese sem calibração de campo. Não há árvores, paredes, relevo\nou sombreamento aleatório explícitos no modelo.',85,540,1110,100,29,muted);
}
// 8
{
 const s=slide('Métricas e tratamento dos dados','Fonte: src/manet-routing.cc, scripts/analyze.py e article/main.tex seção 3.2. PDR usa demanda nominal, não contador de geração real do OnOff. Vazão inclui entregas até 120 s, divididas por 90 s. Atraso começa na observação IP. Jitter usa soma por fluxo de max(rx-1,0). IC t de 95% entre runs, não entre pacotes. Seis runs sem recepção em 700 m têm atraso/jitter indefinidos.');
 table(s,[['Métrica','Definição'],['PDR (%)','100 × recebidos / demanda nominal de 1436 pacotes'],['Vazão (Mbps)','Bytes de aplicação recebidos × 8 / 90 s / 10⁶'],['Atraso (ms)','Σ delaySum / Σ recebidos, desde a observação IP'],['Jitter (ms)','Σ jitterSum / Σ max(recebidos − 1, 0), por fluxo']],{h:330,widths:[280,840],size:25});
 text(s,'Média e IC de 95% entre runs independentes',85,535,1110,45,29,cyan);
 text(s,'Atraso e jitter consideram apenas entregas. Sem amostras, são indefinidos.',85,605,1110,65,25,muted);
}
// 9
{
 const s=slide('Variável adicional: área','Fonte: configuração em scripts/run-area-experiments.sh. Densidades calculadas como 20 / área em km². O expoente é fixo em 2,7. A área também muda os tempos de travessia, e não apenas a densidade.');
 table(s,[['Dimensões','Área (km²)','Densidade (nós/km²)'],['300 × 300 m','0,09','222,2'],['500 × 500 m','0,25','80,0'],['700 × 700 m','0,49','40,8']],{y:190,h:270,widths:[400,300,420],size:29});
 lines(s,['20 nós e rádio fixo em todos os níveis','A área altera distâncias, densidade e tempos de travessia'],520,28,70);
}
// 10
{
 const s=slide('PDR e vazão no cenário-base','Fonte: data/processed/area/resumo-estatistico.csv, área 500 m. Curvas de médias, barras IC t de 95%, n=20 por configuração. As barras são inseridas como erros personalizados nativos no PPTX a partir das colunas *_ci95.');
 chart(s,500,'pdr','PDR',55,170,565,420,100,'%');
 chart(s,500,'throughputMbps','Vazão',660,170,565,420,0.14,'Mbps');
 text(s,'Médias e IC de 95%, 20 runs por configuração. A vazão acompanha a entrega.',75,625,1140,50,25,muted);
}
// 11
{
 const s=slide('Atraso e jitter no cenário-base','Fonte: data/processed/area/resumo-estatistico.csv, área 500 m. A latência é condicionada à entrega. Não permite concluir superioridade sem considerar as perdas.');
 chart(s,500,'delayMs','Atraso médio',55,170,565,420,200,'ms');
 chart(s,500,'jitterMs','Jitter médio',660,170,565,420,90,'ms');
 text(s,'Médias e IC de 95%. Perdas podem retirar os pacotes mais demorados das médias.',75,625,1140,50,25,muted);
}
// 12
{
 const s=slide('Comparação a 10 m/s','Fonte: data/processed/area/resumo-estatistico.csv, área 500 m e velocidade 10 m/s. Cada célula mostra média ± semiamplitude do IC t de 95% entre 20 runs. Não é um teste pareado de significância.');
 const metrics=[['PDR (%)','pdr',1],['Vazão (Mbps)','throughputMbps',3],['Atraso (ms)','delayMs',1],['Jitter (ms)','jitterMs',1]];
 const values=[['Métrica',...protocols],...metrics.map(([name,m,d])=>[name,...protocols.map(p=>`${fmt(row(500,p,10)[m+'_mean'],d)} ± ${fmt(row(500,p,10)[m+'_ci95'],d)}`)])];
 table(s,values,{y:185,h:345,widths:[310,270,270,270],size:28});
 text(s,'Área-base de 500 × 500 m. Média ± IC de 95%.',85,570,1110,45,27,muted);
 text(s,'AODV entrega mais pacotes, com maior atraso médio nessa condição.',85,630,1110,45,27,cyan);
}
// 13
{
 const s=slide('Efeito da área sobre o PDR','Fonte: data/processed/area/resumo-estatistico.csv, três áreas. Mesmos parâmetros de rádio e propagação. Barras IC t de 95%, n=20. Em 700 m o PDR médio do AODV sobe de 35,5% a 1 m/s para 52,2% a 5 m/s. O efeito de encontros/transiente não foi isolado.');
 [300,500,700].forEach((a,i)=>chart(s,a,'pdr',`${a} × ${a} m`,45+i*410,170,390,390,100,'%'));
 text(s,'A 20 m/s, o AODV entrega 87,2%, 66,3% e 37,3% nas três áreas.',75,590,1140,45,28,cyan);
 text(s,'Em 700 m, a entrega melhora de 1 para 5 m/s e depois cai.',75,650,1140,45,26,muted);
}
// 14
{
 const s=slide('Conclusões e limites','Fontes: article/resultados.tex; article/main.tex, conclusão; docs/revisao-metodologica.md. Sem teste de significância pareado. Não se atribui causalidade exclusiva às rotas. O código, dados e artigo são publicados no repositório do grupo.');
 lines(s,['No base, maior velocidade reduz o PDR dos três protocolos.','A 20 m/s, ampliar a área reduz a entrega com o rádio fixo.','A tendência com a velocidade depende da área.'],170,31,95);
 text(s,'Limites: 20 nós, tráfego leve, expoente 2,7 sem calibração.\nO aquecimento de 20 s não garante regime estacionário.\nO estudo não prevê a cobertura de um local real.',85,475,1110,130,27,muted);
 const sh=text(s,'github.com/EduardoFerreiraB/Redes-Moveis',85,640,1120,45,27,cyan);
 sh.text.get('github.com/EduardoFerreiraB/Redes-Moveis').link={uri:'https://github.com/EduardoFerreiraB/Redes-Moveis',isExternal:true};
}
await fs.writeFile(path.join(out,'chart-errors.json'),JSON.stringify(chartErrors,null,2));
await (await PresentationFile.exportPptx(deck)).save(path.join(out,'draft.pptx'));
await fs.writeFile(path.join(out,'deck.json'),JSON.stringify(deck.toProto()));
console.log(JSON.stringify({slides:deck.slides.items.length,charts:chartErrors.length,out}));
