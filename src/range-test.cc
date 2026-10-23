/*
 * SPDX-License-Identifier: GPL-2.0-only
 *
 * Teste de alcance do rádio usado no cenário MANET (src/manet-routing.cc).
 *
 * Dois nós parados a --distance metros; o nó 1 envia --packets pacotes UDP
 * unicast de 1024 bytes ao nó 0, um a cada 50 ms. A camada física é a mesma
 * do cenário principal: IEEE 802.11b ad hoc a 11 Mb/s, perda de Friis e
 * potência --txPower. Imprime "distancia,potencia,enviados,recebidos,taxa".
 *
 * Uso típico (ver scripts/range-test.sh):
 *   ./ns3 run "range-test --distance=150 --txPower=7.5"
 */

#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/mobility-module.h"
#include "ns3/network-module.h"
#include "ns3/yans-wifi-helper.h"

#include <iostream>

using namespace ns3;

static uint32_t g_received = 0;

static void
ReceivePacket(Ptr<Socket> socket)
{
    while (socket->Recv())
    {
        g_received++;
    }
}

int
main(int argc, char* argv[])
{
    double distance = 100.0;
    double txPower = 7.5;
    uint32_t packets = 200;
    uint32_t packetSize = 1024;

    CommandLine cmd(__FILE__);
    cmd.AddValue("distance", "Distance between the two nodes (m)", distance);
    cmd.AddValue("txPower", "Transmission power (dBm)", txPower);
    cmd.AddValue("packets", "Number of packets to send", packets);
    cmd.AddValue("packetSize", "UDP payload size (bytes)", packetSize);
    cmd.Parse(argc, argv);

    std::string phyMode("DsssRate11Mbps");
    Config::SetDefault("ns3::WifiRemoteStationManager::NonUnicastMode", StringValue(phyMode));

    NodeContainer nodes;
    nodes.Create(2);

    WifiHelper wifi;
    wifi.SetStandard(WIFI_STANDARD_80211b);
    YansWifiPhyHelper wifiPhy;
    YansWifiChannelHelper wifiChannel;
    wifiChannel.SetPropagationDelay("ns3::ConstantSpeedPropagationDelayModel");
    wifiChannel.AddPropagationLoss("ns3::FriisPropagationLossModel");
    wifiPhy.SetChannel(wifiChannel.Create());
    wifiPhy.Set("TxPowerStart", DoubleValue(txPower));
    wifiPhy.Set("TxPowerEnd", DoubleValue(txPower));
    wifi.SetRemoteStationManager("ns3::ConstantRateWifiManager",
                                 "DataMode",
                                 StringValue(phyMode),
                                 "ControlMode",
                                 StringValue(phyMode));
    WifiMacHelper wifiMac;
    wifiMac.SetType("ns3::AdhocWifiMac");
    NetDeviceContainer devices = wifi.Install(wifiPhy, wifiMac, nodes);

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> positions = CreateObject<ListPositionAllocator>();
    positions->Add(Vector(0, 0, 0));
    positions->Add(Vector(distance, 0, 0));
    mobility.SetPositionAllocator(positions);
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    mobility.Install(nodes);

    InternetStackHelper internet;
    internet.Install(nodes);
    Ipv4AddressHelper address;
    address.SetBase("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer interfaces = address.Assign(devices);

    uint16_t port = 9;
    Ptr<Socket> sink = Socket::CreateSocket(nodes.Get(0), UdpSocketFactory::GetTypeId());
    sink->Bind(InetSocketAddress(Ipv4Address::GetAny(), port));
    sink->SetRecvCallback(MakeCallback(&ReceivePacket));

    UdpClientHelper client(interfaces.GetAddress(0), port);
    client.SetAttribute("MaxPackets", UintegerValue(packets));
    client.SetAttribute("Interval", TimeValue(MilliSeconds(50)));
    client.SetAttribute("PacketSize", UintegerValue(packetSize));
    ApplicationContainer apps = client.Install(nodes.Get(1));
    apps.Start(Seconds(1.0));

    Simulator::Stop(Seconds(2.0 + packets * 0.05));
    Simulator::Run();
    Simulator::Destroy();

    std::cout << distance << "," << txPower << "," << packetSize << "," << packets << ","
              << g_received << "," << 100.0 * g_received / packets << std::endl;
    return 0;
}
