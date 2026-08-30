# VirtualBox Networking — A Foundational Guide

*Understand how your VMs talk to your computer and the internet, with real command-line examples.*

---

## 1. The Big Picture

Every VirtualBox VM has up to **8 virtual network cards (NICs)**. Each one can be set to a different **mode**, and the mode decides:
- Can the VM reach the internet?
- Can the VM reach your host computer?
- Can the VM reach *other* VMs?
- Can the outside world reach *into* the VM?

Think of each mode as a different type of **wall** built around your VM, with different-sized doors in it.

You configure a NIC's mode two ways:
- **GUI:** VM → Settings → Network → Attached to
- **Command line:**
```bash
VBoxManage modifyvm "VM name" --nic1 <mode>
```
`nic1` means "the first network card." Use `nic2`, `nic3`, etc. for additional cards.

---

## 2. The Modes at a Glance

| Mode | VM → Host | Host → VM | VM ↔ VM | VM → Internet | Internet → VM |
|---|:---:|:---:|:---:|:---:|:---:|
| **NAT** *(default)* | ✅ | 🔶 port-forward only | ❌ | ✅ | ❌ |
| **NAT Network** | ✅ | 🔶 port-forward only | ✅ | ✅ | ❌ |
| **Bridged** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Internal** | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Host-only** | ✅ | ✅ | ✅ | ❌ | ❌ |

🔶 = only works if you set up a specific rule.

---

## 3. NAT — "The VM goes out through you, alone"

**This is the default mode.** Your VM acts like a laptop plugged into a home router — it can browse the internet freely, but nobody outside can reach in.

```
┌──────────────────────────────────────┐
│              Host machine            │
│  ┌──────────────┐   ┌──────────────┐ │
│  │ NAT engine   │──▶│  Guest VM    │ │
│  │(like a router)│  │ 10.0.2.x     │ │
│  └──────────────┘   └──────────────┘ │
└──────────────────────────────────────┘
              │
              ▼
          Internet
```

- **Use it for:** browsing, downloading, checking email inside the VM.
- **Limitation:** you can't run a server (like SSH or a website) that others can reach — unless you forward a port.



## 4. Bridged Networking — "The VM becomes a real device on your network"

Bridged mode makes the VM act like a **separate physical computer plugged directly into your router/switch**. It gets its own IP address on your home/office network.

```
┌────────────┐     ┌────────────┐     ┌────────────┐
│  Your PC   │     │  Guest VM  │     │  Router    │
│ 192.168.1.5│     │192.168.1.9 │◀───▶│           │
└────────────┘     └────────────┘     └────────────┘
        both connect directly to the same network
```

- **Use it for:** running a server others need to reach, testing real network behavior, network simulations.
- **Setup:** pick your physical adapter (Wi-Fi or Ethernet) as the "bridge."


---

## 5. Internal Networking — "A private club for VMs only"

VMs can talk to each other, but **nothing else can see them** — not your host, not the internet.

```
┌──────────────┐        ┌──────────────┐
│   VM 1       │◀──────▶│   VM 2      │
└──────────────┘        └──────────────┘
        (both on internal network "intnet")
        host and internet: no access
```

- **Use it for:** simulating a private network between two VMs (e.g. a web server VM talking privately to a database VM), security testing.


---

## 6. Host-Only Networking — "A private club that includes you"

Same as Internal, but your **host machine is also invited**. The VM(s) and your host can all talk to each other, but nobody can reach the internet through this adapter.

```
┌────────────┐     ┌──────────────┐     ┌──────────────┐
│  Your PC   │◀───▶│   VM 1      │◀───▶│   VM 2      │
└────────────┘     └──────────────┘     └──────────────┘
           all connected, no internet access
```

- **Use it for:** testing an app on the VM from your host browser, connecting a database VM and web-server VM together while keeping them offline.



---

## 7. NAT Network — "NAT, but VMs can see each other too"

A middle ground: like NAT (internet access, invisible from outside), but multiple VMs attached to the same NAT Network *can* talk to each other — unlike plain NAT mode.

Then attach VMs to it via Settings → Network → Attached to → **NAT Network** → `natnet1`.

---

## 8. Quick Decision Guide

```
Do other VMs need to talk to this VM?
│
├─ No → Just need internet? ────────────────► NAT (default)
│
└─ Yes ─┬─ Do they need internet too? ──────► NAT Network
        │
        └─ Does your HOST need to join in? 
             ├─ Yes ──────────────────────────► Host-only
             └─ No ───────────────────────────► Internal

Need the outside world (or your router/LAN) to reach the VM directly?
                                             ► Bridged
```

---

## 9. Cheat Sheet — Common Commands

| Task | Command |
|---|---|
| Set NIC 1 to NAT | `VBoxManage modifyvm "VM" --nic1 nat` |
| Set NIC 1 to Bridged | `VBoxManage modifyvm "VM" --nic1 bridged --bridgeadapter1 "Ethernet"` |
| Set NIC 1 to Internal | `VBoxManage modifyvm "VM" --nic1 intnet --intnet1 "netname"` |
| Set NIC 1 to Host-only | `VBoxManage modifyvm "VM" --nic1 hostonly` |
| Forward a port (NAT) | `VBoxManage modifyvm "VM" --nat-pf1 "name,tcp,,HOSTPORT,,GUESTPORT"` |
| Delete a port-forward rule | `VBoxManage modifyvm "VM" --natpf1 delete "name"` |
| Create a NAT Network | `VBoxManage natnetwork add --netname NAME --network "CIDR" --enable` |
| List NAT Networks | `VBoxManage list natnetworks` |

---

## 10. Summary

- **NAT** (default) — VM gets internet, nobody gets in, unless you forward a port.
- **Bridged** — VM becomes a real device on your physical network.
- **Internal** — VMs talk to each other only, fully isolated.
- **Host-only** — VMs + your host can talk, no internet.
- **NAT Network** — like NAT, but VMs can also see each other.

Every mode is a trade-off between **isolation** (safer, more private) and **reachability** (more useful, more exposed). Start with NAT for everyday use, and switch modes only when you have a specific reason — testing a server, connecting VMs together, or simulating a real network.
