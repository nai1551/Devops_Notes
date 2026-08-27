# Linux File System Explained

Linux ফাইল সিস্টেমের হায়ারার্কি (FHS - Filesystem Hierarchy Standard) কীভাবে সাজানো, তার ব্যাখ্যা।

**Source:** [ByteByteGo — Linux File System Explained](https://bytebytego.com/guides/linux-file-system-explained/)

![Linux File System Diagram](./assets/linux-file-system-explained.jpg)

---

## History & Background

আগে Linux-এর ফাইল সিস্টেম ছিল একটা অগোছালো শহরের মতো, যেখানে যে যার ইচ্ছামতো ঘর বানাইতো। কিন্তু **১৯৯৪ সালে** চালু হয় **Filesystem Hierarchy Standard (FHS)**, যেইটা Linux ফাইল সিস্টেমে একটা শৃঙ্খলা নিয়া আসে।

FHS-এর মতো একটা স্ট্যান্ডার্ড থাকার কারণে সফটওয়্যার বিভিন্ন Linux ডিস্ট্রিবিউশনে একই রকম লেআউট বজায় রাখতে পারে — তবে সব ডিস্ট্রো এই স্ট্যান্ডার্ড কড়াকড়িভাবে মানে না; অনেক সময় নিজেদের প্রয়োজন অনুযায়ী কিছু পরিবর্তন করে।

গোটা ফাইল সিস্টেমটাকে একটা **tree** হিসেবে কল্পনা করা যায়, যার শুরু root (`/`) থেকে। `cd` দিয়ে নেভিগেট আর `ls` দিয়ে ডিরেক্টরি দেখতে দেখতে এইটা ধীরে ধীরে সহজ হয়ে যায়।

---

## Directory Reference

| ডিরেক্টরি | কাজ (English) | ব্যাখ্যা (বাংলা) |
|---|---|---|
| `/bin` | Essential command binaries | `ls`, `cp`, `mv`-এর মতো দরকারি কমান্ড এখানে থাকে |
| `/boot` | System boot loader files | কার্নেল ও GRUB-এর মতো বুট ফাইল |
| `/dev` | Device files | হার্ডওয়্যার ডিভাইস ফাইল হিসেবে represent করা হয় |
| `/etc` | Host-specific system-wide configuration files | পুরা সিস্টেমের কনফিগারেশন ফাইল |
| `/home` | User home directory | সাধারণ ইউজারদের ব্যক্তিগত ফোল্ডার |
| `/lib` | Shared library modules | প্রোগ্রাম চালানোর জন্য দরকারি shared library |
| `/media` | Media file such as CD-ROM | রিমুভেবল মিডিয়া মাউন্ট হওয়ার জায়গা |
| `/mnt` | Temporary mounted filesystems | এক্সটার্নাল ড্রাইভ সাময়িক মাউন্ট করার জায়গা |
| `/opt` | Add-on application software packages | থার্ড-পার্টি সফটওয়্যার প্যাকেজ |
| `/proc` | Interface to kernel data structures | virtual ডিরেক্টরি, কার্নেলের ডেটা অ্যাক্সেস করার জন্য |
| `/root` | Home directory for root user | root ইউজারের হোম ডিরেক্টরি |
| `/run` | Run-time program data | বুট হওয়ার পর তৈরি হওয়া রানটাইম ডেটা |
| `/sbin` | System binaries | অ্যাডমিনিস্ট্রেটিভ কাজের বাইনারি |
| `/srv` | Site-specific data served by this system | সার্ভার থেকে serve করা ডেটা |
| `/sys` | Virtual directory providing information about the system | কার্নেল/ডিভাইস সম্পর্কিত virtual ফাইলসিস্টেম |
| `/tmp` | Temporary files | সাময়িক ফাইল, রিবুটে মুছে যায় |
| `/usr` | Unix System Resources | ইউজার-লেভেল প্রোগ্রাম ও লাইব্রেরির প্রধান জায়গা |
| `/var` | File that is expected to continuously change | লগ, ক্যাশের মতো ক্রমাগত পরিবর্তনশীল ডেটা |

---

## Quick Notes

- পুরা সিস্টেম **একটাই root (`/`)** থেকে শুরু হয় — Windows-এর মতো আলাদা আলাদা ড্রাইভ লেটার (C:, D:) নাই।
- `/bin`, `/sbin`, `/lib` আধুনিক ডিস্ট্রোতে (যেমন Ubuntu/Fedার নতুন ভার্সনে) প্রায়ই `/usr` এর ভেতরে symlink করা থাকে (`/usr/bin` ইত্যাদি) — একে বলে **UsrMerge**।
- `/proc` আর `/sys` কোনো ডিস্কে সেভ থাকে না, এগুলা কার্নেল রিয়েল-টাইমে জেনারেট করে — একে বলে **virtual/pseudo filesystem**।
- `/etc`-এর নাম নিয়ে মজার একটা কথা প্রচলিত আছে: "et cetera" (বাকি সব) থেকে এসেছে, কারণ যা কোথাও ফিট করে না, তা এখানে রাখা হতো।

---

*Reference: [bytebytego.com/guides/linux-file-system-explained](https://bytebytego.com/guides/linux-file-system-explained/)*
