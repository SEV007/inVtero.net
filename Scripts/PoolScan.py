##########################################################################
#
# Demo of how to pool scan with python CLI
# Most of this converted from windbg module from https://github.com/fishstiqz/poolinfo
#
##########################################################################
import clr
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

clr.AddReferenceToFileAndPath("inVtero.net.dll")

from inVtero.net import *
from System import Environment, String, Console, ConsoleColor, BitConverter 
from inVtero.net.Support import Strings
from System.Text.RegularExpressions import Regex, RegexOptions
from System.Text import Encoding

#FileName = "C:\\temp\\server2016.xendump"   
#FileName = "C:\\temp\\2012R2.debug.MEMORY.DMP"   
#vtero = QuickSetup(FileName)

#########################################################################
# This is a utility function for following/dumping chunks
#########################################################################
def PrintChunk(p, Addr):
    pHeader = p.xStructInfo("_POOL_HEADER", Addr)
    prevSize = pHeader.PreviousSize.Value << 4
    Size = pHeader.BlockSize.Value << 4
    Addr = pHeader.vAddress
    print "Address: " + Addr.ToString("X") + " Size: " + Size.ToString("X"),
    print " previous size: " + prevSize.ToString("X") + " Tag: " + Encoding.ASCII.GetString(BitConverter.GetBytes(pHeader.PoolTag.Value))
    return Size

def PoolInfo(vtero):
    p = vtero.KernelProc
    # lists to hold set's
    NPPoolDescs = []
    PPoolDescs = []
    #########################################################################
    # get typedefs mostly for length checks
    #########################################################################
    POOL_DESC = p.xStructInfo("_POOL_DESCRIPTOR")
    POOL_HEAD = p.xStructInfo("_POOL_HEADER")
    pcrbDef = p.xStructInfo("_KPRCB")
    #########################################################################
    # Processor control block info is handy (others also ExpSessionPoolLookaside) 
    #########################################################################
    # KiProcessorBlock[CPUCount] == array of _KPRCB
    numProcs = p.GetSymValueLong("KeNumberProcessors") & 0xff
    KPRCB = p.xStructInfo("_KPRCB", p.GetSymValueLong("KiProcessorBlock"), pcrbDef.Length)
    print Encoding.ASCII.GetString(KPRCB.VendorString.Value)
    # e.g. how to walk _KTHREAD from here / find all other KPRCB
    NextThread = p.xStructInfo("_KTHREAD", KPRCB.NextThread.vAddress)
    GeneralLookaside = p.xStructInfo("_GENERAL_LOOKASIDE", KPRCB.PPNPagedLookasideList.vAddress)
    #########################################################################
    # Paged Pool info
    #########################################################################
    NumPaged  = p.GetSymValueLong("ExpNumberOfPagedPools") + 1
    kDescList  = p.GetSymValueLong("ExpPagedPoolDescriptor")
    for x in range(0, numProcs):
        PPoolDescs.append(p.xStructInfo("_POOL_DESCRIPTOR", kDescList + (x*8)))
    #########################################################################
    # NonPaged Pools follow CPU count
    #########################################################################
    kNonPDescList = p.GetSymValueLong("ExpNonPagedPoolDescriptor")
    kVectorBase = p.GetSymValueLong("PoolVector")
    for x in range(0, numProcs):
        NPPoolDescs.append(p.xStructInfo("_POOL_DESCRIPTOR", kNonPDescList + (x*8)))
    # get the first NP pool descriptor
    npDesc = NPPoolDescs[0]
    # were on the POOL_HEADER pointer now
    npChunkPtr = npDesc.vAddress + npDesc.ListHeads.OffsetPos  + 0x10 
    #########################################################################
    # Parse the entire set of chunk's allocation's by following the links
    # This should dump out the entire pool page allocation set
    #########################################################################
    for x in range(0, 512):
        npChunk = p.GetLongValue(npChunkPtr + (x * 8))
        Addr = npChunk - POOL_HEAD.Length
        Size = PrintChunk(p, Addr)
        while Size > 0:
            Addr = Addr + Size
            Size = PrintChunk(p, Addr)


#########################################################################
# "strings" like functionality (UNICODE/UTF8/ASCII) modes/regex
#########################################################################
def strings(p, rx):
    regx = Regex(rx, RegexOptions.Compiled)
    for s in Strings.SimpleRegex(regx, p):
        print s.Item1.ToString("X") + " " + s.Item2

#########################################################################
# This is a FULL address space search (bytescan)
#########################################################################
def scan(p, toFind, align = 4, Kernel = False):
    for addr in Strings.ByteScan(Encoding.ASCII.GetBytes(toFind), p, align, Kernel):
        print addr.ToString("X")
#########################################################################
# example pull in one of the ListHeads from System import BitConverter
# BitConverter.ToUInt64(np.ListHeads.Value, 0).ToString("X")
#########################################################################
def scanq(p, toFind, align = 4, Kernel = False):
    for addr in Strings.QWordScan(toFind, p, align, Kernel):
        print addr.ToString("X")