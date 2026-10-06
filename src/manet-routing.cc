/*
 * Copyright (c) 2011 University of Kansas
 *
 * SPDX-License-Identifier: GPL-2.0-only
 *
 * Author: Justin Rohrer <rohrej@ittc.ku.edu>
 *
 * James P.G. Sterbenz <jpgs@ittc.ku.edu>, director
 * ResiliNets Research Group  https://resilinets.org/
 * Information and Telecommunication Technology Center (ITTC)
 * and Department of Electrical Engineering and Computer Science
 * The University of Kansas Lawrence, KS USA.
 *
 * Work supported in part by NSF FIND (Future Internet Design) Program
 * under grant CNS-0626918 (Postmodern Internet Architecture),
 * NSF grant CNS-1050226 (Multilayer Network Resilience Analysis and Experimentation on GENI),
 * US Department of Defense (DoD), and ITTC at The University of Kansas.
 */

/*
 * Cenário MANET do trabalho de Redes Móveis (IFG Inhumas, 2026/2), adaptado
 * do exemplo examples/routing/manet-routing-compare.cc do ns-3.
 *
 * Cenário base (enunciado da atividade):
 * - 20 nós em 500 x 500 m, IEEE 802.11b ad hoc a 11 Mb/s, perda de Friis,
 *   potência de transmissão de 7,5 dBm;
 * - mobilidade RandomWaypointMobilityModel com velocidade constante
 *   (--speed) e tempo de pausa (--pause);
 * - 4 fluxos UDP (OnOff sempre ligado) de 32768 b/s com pacotes de 1024 bytes:
 *   o nó i + flows envia para o nó i; tráfego entre 20 s e 110 s;
 * - 120 s de simulação;
 * - roteamento AODV, OLSR ou DSDV (--protocol).
 *
 * Aleatoriedade: --seed e --run alimentam o RngSeedManager do ns-3. Com a
 * mesma seed/run, todos os protocolos recebem o mesmo padrão de mobilidade
 * (streams fixos via AssignStreams), o que torna a comparação pareada.
 *
 * Saídas, gravadas em --outDir:
 * - resumo.csv: uma linha com parâmetros e métricas da execução
 *   (pacotes, PDR, vazão, atraso e jitter, considerando só os fluxos de dados);
 * - vazao-por-segundo.csv: vazão recebida a cada segundo;
 * - flowmon.xml: estatísticas brutas do FlowMonitor (inclui tráfego de controle);
 * - mobilidade.mob: trajetória dos nós (somente com --traceMobility=true).
 */

#include "ns3/aodv-module.h"
#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/dsdv-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/internet-module.h"
#include "ns3/mobility-module.h"
#include "ns3/network-module.h"
#include "ns3/olsr-module.h"
#include "ns3/yans-wifi-helper.h"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("manet-routing");

/**
 * Routing experiment class.
 *
 * It handles the creation and run of an experiment.
 */
class RoutingExperiment
{
  public:
    /**
     * Run the experiment.
     */
    void Run();

    /**
     * Handles the command-line parameters.
     * @param argc The argument count.
     * @param argv The argument vector.
     */
    void CommandSetup(int argc, char** argv);

  private:
    /**
     * Setup the receiving socket in a Sink Node.
     * @param addr The address of the node.
     * @param node The node pointer.
     * @return the socket.
     */
    Ptr<Socket> SetupPacketReceive(Ipv4Address addr, Ptr<Node> node);
    /**
     * Receive a packet.
     * @param socket The receiving socket.
     */
    void ReceivePacket(Ptr<Socket> socket);
    /**
     * Count a packet sent by a source application.
     * @param packet The packet.
     */
    void SendPacket(Ptr<const Packet> packet);
    /**
     * Compute the throughput of the last second.
     */
    void CheckThroughput();
    /**
     * Write the per-run summary (parameters and metrics) to resumo.csv.
     * @param flowmon The flow monitor.
     * @param classifier The flow classifier.
     */
    void WriteSummary(Ptr<FlowMonitor> flowmon, Ptr<Ipv4FlowClassifier> classifier);

    uint16_t port{9};               //!< Receiving port number of the data flows.
    uint32_t bytesTotal{0};         //!< Bytes received in the current second.
    uint32_t packetsReceived{0};    //!< Packets received in the current second.
    uint64_t m_appTxPackets{0};     //!< Data packets sent by the applications.
    uint64_t m_appRxPackets{0};     //!< Data packets received by the sinks.
    uint64_t m_appRxBytes{0};       //!< Data bytes received by the sinks.

    std::string m_protocolName{"AODV"}; //!< Protocol name.
    double m_speed{1.0};                //!< Node speed (m/s).
    double m_pause{0.0};                //!< Node pause time (s).
    uint32_t m_nodes{20};               //!< Number of nodes.
    uint32_t m_flows{4};                //!< Number of source/sink pairs.
    double m_area{500.0};               //!< Side of the square area (m).
    uint32_t m_packetSize{1024};        //!< Application packet size (bytes).
    std::string m_dataRate{"32768bps"}; //!< Application data rate per flow.
    double m_txp{7.5};                  //!< Tx power (dBm).
    uint32_t m_seed{1};                 //!< RNG seed.
    uint64_t m_run{1};                  //!< RNG run number.
    double m_totalTime{120.0};          //!< Simulation time (s).
    double m_appStart{20.0};            //!< Traffic start (s).
    double m_appStop{110.0};            //!< Traffic stop (s).
    std::string m_outDir{"."};          //!< Output directory.
    bool m_traceMobility{false};        //!< Enable mobility tracing.
    bool m_verbose{false};              //!< Print every received packet.
};

static inline std::string
PrintReceivedPacket(Ptr<Socket> socket, Ptr<Packet> packet, Address senderAddress)
{
    std::ostringstream oss;

    oss << Simulator::Now().GetSeconds() << " " << socket->GetNode()->GetId();

    if (InetSocketAddress::IsMatchingType(senderAddress))
    {
        InetSocketAddress addr = InetSocketAddress::ConvertFrom(senderAddress);
        oss << " received one packet from " << addr.GetIpv4();
    }
    else
    {
        oss << " received one packet!";
    }
    return oss.str();
}

void
RoutingExperiment::ReceivePacket(Ptr<Socket> socket)
{
    Ptr<Packet> packet;
    Address senderAddress;
    while ((packet = socket->RecvFrom(senderAddress)))
    {
        bytesTotal += packet->GetSize();
        packetsReceived += 1;
        m_appRxPackets += 1;
        m_appRxBytes += packet->GetSize();
        if (m_verbose)
        {
            NS_LOG_UNCOND(PrintReceivedPacket(socket, packet, senderAddress));
        }
    }
}

void
RoutingExperiment::SendPacket(Ptr<const Packet> packet)
{
    m_appTxPackets += 1;
}

void
RoutingExperiment::CheckThroughput()
{
    double kbs = (bytesTotal * 8.0) / 1000;
    bytesTotal = 0;

    std::ofstream out(m_outDir + "/vazao-por-segundo.csv", std::ios::app);

    out << (Simulator::Now()).GetSeconds() << "," << kbs << "," << packetsReceived << ","
        << m_flows << "," << m_protocolName << "," << m_txp << std::endl;

    out.close();
    packetsReceived = 0;
    Simulator::Schedule(Seconds(1), &RoutingExperiment::CheckThroughput, this);
}

Ptr<Socket>
RoutingExperiment::SetupPacketReceive(Ipv4Address addr, Ptr<Node> node)
{
    TypeId tid = TypeId::LookupByName("ns3::UdpSocketFactory");
    Ptr<Socket> sink = Socket::CreateSocket(node, tid);
    InetSocketAddress local = InetSocketAddress(addr, port);
    sink->Bind(local);
    sink->SetRecvCallback(MakeCallback(&RoutingExperiment::ReceivePacket, this));

    return sink;
}

void
RoutingExperiment::CommandSetup(int argc, char** argv)
{
    CommandLine cmd(__FILE__);
    cmd.AddValue("protocol", "Routing protocol (AODV, OLSR, DSDV)", m_protocolName);
    cmd.AddValue("speed", "Node speed in m/s", m_speed);
    cmd.AddValue("pause", "Node pause time in s", m_pause);
    cmd.AddValue("nodes", "Number of nodes", m_nodes);
    cmd.AddValue("flows", "Number of UDP source/sink pairs", m_flows);
    cmd.AddValue("area", "Side of the square simulation area in m", m_area);
    cmd.AddValue("packetSize", "Application packet size in bytes", m_packetSize);
    cmd.AddValue("dataRate", "Application data rate per flow", m_dataRate);
    cmd.AddValue("txPower", "Transmission power in dBm", m_txp);
    cmd.AddValue("seed", "RNG seed (RngSeedManager::SetSeed)", m_seed);
    cmd.AddValue("run", "RNG run number (RngSeedManager::SetRun)", m_run);
    cmd.AddValue("outDir", "Directory for the output files", m_outDir);
    cmd.AddValue("traceMobility", "Enable mobility tracing", m_traceMobility);
    cmd.AddValue("verbose", "Print every received packet", m_verbose);
    cmd.Parse(argc, argv);

    std::vector<std::string> allowedProtocols{"AODV", "OLSR", "DSDV"};
    if (std::find(allowedProtocols.begin(), allowedProtocols.end(), m_protocolName) ==
        allowedProtocols.end())
    {
        NS_FATAL_ERROR("No such protocol: " << m_protocolName);
    }
    if (m_speed <= 0)
    {
        NS_FATAL_ERROR("speed must be greater than zero");
    }
    if (2 * m_flows > m_nodes)
    {
        NS_FATAL_ERROR("flows must be at most nodes / 2 (each flow uses two distinct nodes)");
    }
}

void
RoutingExperiment::WriteSummary(Ptr<FlowMonitor> flowmon, Ptr<Ipv4FlowClassifier> classifier)
{
    // Somente os fluxos de dados (porta de destino 9). O FlowMonitor também
    // registra o tráfego de controle dos protocolos (ex.: AODV na porta 654).
    uint64_t fmTx = 0;
    uint64_t fmRx = 0;
    uint64_t jitterSamples = 0;
    double delaySum = 0;
    double jitterSum = 0;
    for (const auto& [flowId, st] : flowmon->GetFlowStats())
    {
        if (classifier->FindFlow(flowId).destinationPort != port)
        {
            continue;
        }
        fmTx += st.txPackets;
        fmRx += st.rxPackets;
        delaySum += st.delaySum.GetSeconds();
        jitterSum += st.jitterSum.GetSeconds();
        jitterSamples += st.rxPackets > 1 ? st.rxPackets - 1 : 0;
    }

    // Pacotes gerados: um a cada packetSize*8/dataRate segundos, por fluxo,
    // enquanto a aplicação está ativa. Quando não há rota (ex.: OLSR antes de
    // convergir), o OnOffApplication não consegue enviar e retém o pacote para
    // a próxima tentativa; esses pacotes não aparecem no FlowMonitor nem no
    // trace "Tx". Por isso PDR e perdas são calculados sobre os gerados.
    double slotsPerFlow = (m_appStop - m_appStart) * DataRate(m_dataRate).GetBitRate() /
                          (m_packetSize * 8.0);
    uint64_t generated = m_flows * static_cast<uint64_t>(std::ceil(slotsPerFlow - 1e-9) - 1);
    uint64_t lost = generated - m_appRxPackets;
    double pdr = generated ? 100.0 * m_appRxPackets / generated : 0;
    double throughputMbps = m_appRxBytes * 8.0 / (m_appStop - m_appStart) / 1e6;
    double delayMs = fmRx ? 1000 * delaySum / fmRx : 0;
    double jitterMs = jitterSamples ? 1000 * jitterSum / jitterSamples : 0;

    std::ofstream out(m_outDir + "/resumo.csv");
    out << "protocol,speed,pause,nodes,flows,area,packetSize,dataRate,txPower,seed,run,"
        << "generatedPackets,txPackets,rxPackets,lostPackets,pdr,throughputMbps,delayMs,"
        << "jitterMs,flowmonTxPackets,flowmonRxPackets" << std::endl;
    out << m_protocolName << "," << m_speed << "," << m_pause << "," << m_nodes << ","
        << m_flows << "," << m_area << "," << m_packetSize << "," << m_dataRate << ","
        << m_txp << "," << m_seed << "," << m_run << "," << generated << ","
        << m_appTxPackets << "," << m_appRxPackets << "," << lost << "," << pdr << ","
        << throughputMbps << "," << delayMs << "," << jitterMs << "," << fmTx << "," << fmRx
        << std::endl;
    out.close();

    std::cout << m_protocolName << " speed=" << m_speed << " pause=" << m_pause
              << " run=" << m_run << ": gerados=" << generated << " tx=" << m_appTxPackets
              << " rx=" << m_appRxPackets
              << " PDR=" << pdr << "% vazao=" << throughputMbps << " Mbps atraso=" << delayMs
              << " ms jitter=" << jitterMs << " ms" << std::endl;
}

int
main(int argc, char* argv[])
{
    RoutingExperiment experiment;
    experiment.CommandSetup(argc, argv);
    experiment.Run();

    return 0;
}

void
RoutingExperiment::Run()
{
    RngSeedManager::SetSeed(m_seed);
    RngSeedManager::SetRun(m_run);
    std::filesystem::create_directories(m_outDir);

    // blank out the last output file and write the column headers
    std::ofstream out(m_outDir + "/vazao-por-segundo.csv");
    out << "SimulationSecond,"
        << "ReceiveRate,"
        << "PacketsReceived,"
        << "NumberOfSinks,"
        << "RoutingProtocol,"
        << "TransmissionPower" << std::endl;
    out.close();

    std::string phyMode("DsssRate11Mbps");

    Config::SetDefault("ns3::OnOffApplication::PacketSize", UintegerValue(m_packetSize));
    Config::SetDefault("ns3::OnOffApplication::DataRate", StringValue(m_dataRate));

    // Set Non-unicastMode rate to unicast mode
    Config::SetDefault("ns3::WifiRemoteStationManager::NonUnicastMode", StringValue(phyMode));

    NodeContainer adhocNodes;
    adhocNodes.Create(m_nodes);

    // setting up wifi phy and channel using helpers
    WifiHelper wifi;
    wifi.SetStandard(WIFI_STANDARD_80211b);

    YansWifiPhyHelper wifiPhy;
    YansWifiChannelHelper wifiChannel;
    wifiChannel.SetPropagationDelay("ns3::ConstantSpeedPropagationDelayModel");
    wifiChannel.AddPropagationLoss("ns3::FriisPropagationLossModel");
    wifiPhy.SetChannel(wifiChannel.Create());

    // Add a mac and disable rate control
    WifiMacHelper wifiMac;
    wifi.SetRemoteStationManager("ns3::ConstantRateWifiManager",
                                 "DataMode",
                                 StringValue(phyMode),
                                 "ControlMode",
                                 StringValue(phyMode));

    wifiPhy.Set("TxPowerStart", DoubleValue(m_txp));
    wifiPhy.Set("TxPowerEnd", DoubleValue(m_txp));

    wifiMac.SetType("ns3::AdhocWifiMac");
    NetDeviceContainer adhocDevices = wifi.Install(wifiPhy, wifiMac, adhocNodes);

    MobilityHelper mobilityAdhoc;
    int64_t streamIndex = 0; // used to get consistent mobility across scenarios

    std::ostringstream ssArea;
    ssArea << "ns3::UniformRandomVariable[Min=0.0|Max=" << m_area << "]";
    ObjectFactory pos;
    pos.SetTypeId("ns3::RandomRectanglePositionAllocator");
    pos.Set("X", StringValue(ssArea.str()));
    pos.Set("Y", StringValue(ssArea.str()));

    Ptr<PositionAllocator> taPositionAlloc = pos.Create()->GetObject<PositionAllocator>();
    streamIndex += taPositionAlloc->AssignStreams(streamIndex);

    // Velocidade constante (Min = Max) evita o decaimento da velocidade média
    // do Random Waypoint quando a velocidade mínima é próxima de zero.
    std::stringstream ssSpeed;
    ssSpeed << "ns3::ConstantRandomVariable[Constant=" << m_speed << "]";
    std::stringstream ssPause;
    ssPause << "ns3::ConstantRandomVariable[Constant=" << m_pause << "]";
    mobilityAdhoc.SetMobilityModel("ns3::RandomWaypointMobilityModel",
                                   "Speed",
                                   StringValue(ssSpeed.str()),
                                   "Pause",
                                   StringValue(ssPause.str()),
                                   "PositionAllocator",
                                   PointerValue(taPositionAlloc));
    mobilityAdhoc.SetPositionAllocator(taPositionAlloc);
    mobilityAdhoc.Install(adhocNodes);
    streamIndex += mobilityAdhoc.AssignStreams(adhocNodes, streamIndex);

    AodvHelper aodv;
    OlsrHelper olsr;
    DsdvHelper dsdv;
    Ipv4ListRoutingHelper list;
    InternetStackHelper internet;

    if (m_protocolName == "OLSR")
    {
        list.Add(olsr, 100);
    }
    else if (m_protocolName == "AODV")
    {
        list.Add(aodv, 100);
    }
    else if (m_protocolName == "DSDV")
    {
        list.Add(dsdv, 100);
    }
    internet.SetRoutingHelper(list);
    internet.Install(adhocNodes);

    NS_LOG_INFO("assigning ip address");

    Ipv4AddressHelper addressAdhoc;
    addressAdhoc.SetBase("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer adhocInterfaces;
    adhocInterfaces = addressAdhoc.Assign(adhocDevices);

    OnOffHelper onoff1("ns3::UdpSocketFactory", Address());
    onoff1.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1.0]"));
    onoff1.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0.0]"));

    for (uint32_t i = 0; i < m_flows; i++)
    {
        Ptr<Socket> sink = SetupPacketReceive(adhocInterfaces.GetAddress(i), adhocNodes.Get(i));

        AddressValue remoteAddress(InetSocketAddress(adhocInterfaces.GetAddress(i), port));
        onoff1.SetAttribute("Remote", remoteAddress);

        ApplicationContainer temp = onoff1.Install(adhocNodes.Get(i + m_flows));
        temp.Get(0)->TraceConnectWithoutContext(
            "Tx",
            MakeCallback(&RoutingExperiment::SendPacket, this));
        temp.Start(Seconds(m_appStart));
        temp.Stop(Seconds(m_appStop));
    }

    AsciiTraceHelper ascii;
    if (m_traceMobility)
    {
        MobilityHelper::EnableAsciiAll(ascii.CreateFileStream(m_outDir + "/mobilidade.mob"));
    }

    FlowMonitorHelper flowmonHelper;
    Ptr<FlowMonitor> flowmon = flowmonHelper.InstallAll();

    NS_LOG_INFO("Run Simulation.");

    CheckThroughput();

    Simulator::Stop(Seconds(m_totalTime));
    Simulator::Run();

    flowmon->SerializeToXmlFile(m_outDir + "/flowmon.xml", false, false);
    WriteSummary(flowmon, DynamicCast<Ipv4FlowClassifier>(flowmonHelper.GetClassifier()));

    Simulator::Destroy();
}
