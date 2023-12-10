# __Bridge__ - an RIT server security bot
**Bridge** is a Discord bot designed to protect multiple servers against known malicious alternative accounts.

This repository implements an open-sourced version of [ritV](https://github.com/mae-su/ritV/) by [mae.red](https://mae.red), an RIT server security database and library. It exists to protect multiple Discord servers against a growing list of known alternative accounts. 

## Scope: What this project __is__

Bridge is aimed solely against stopping **alt accounts**:
- Accounts created for the purpose of ban evasion
- Spam/advertisement accounts
- Re-use of alt accounts on different servers

Bridge also allows server admins to check what invite link a member joins with.

## Scope: What this project __is not__
Bridge does NOT do any of the following:
- Ban or moderate legitamate members across multiple servers
- Email or identity verification
- Collect information of usual server activity

# How it works
Bridge operates using a database of alternative accounts. New accounts are suggested through **reports** made from within RIT servers. **Reports** are judged by admins of a **Bridge Management Server**, available to join upon request for higher management roles of RIT servers using Bridge. When an account is determined to be an alternative account, Bridge will ban the account by ID across all servers it is in.

# Getting Started
Once Bridge has been invited, run `/setup` to access the Bridge Setup Panel. The Setup Panel will guide you through the steps necessary to get started, and can be run at any time to adjust preferences.

![Bridge Setup Panel](https://cdn.discordapp.com/attachments/1107483500384358510/1183138527463084072/image.png)

***Never* select a publicly available channel or role for these options!**
- **Mod Channel:** for important reports, updates, and RIT server-wide warnings. We recommend using your server's private moderation channel.
- **Log Channel:** for join logs and non-urgent information.
- **Moderator Role:** a role that should be allowed to use `/report`. We recommend setting this to your server's moderator exclusive role.

**Once all values are set,** Bridge will automatically ban all known alternative accounts from your server.

![Bridge log message saying it preemptively banned 46 alternative accounts](https://cdn.discordapp.com/attachments/1107483500384358510/1181467148477005874/image.png)

## Reporting alternative accounts with `/report`

`/report <member> <reason>`

This command will send a request to the Bridge management server to have a suspected alternative account banned.

![Example usage of the altreport command.](cdn.discordapp.com/attachments/1107483500384358510/1183139475145105519/image.png)
### What happens behind the scenes
Reports sent to the Bridge management server contain the following:
- The report's **origin** *(no invite link will be made)*
- The report's **reason**
- A view of **other Bridge servers** that the reported account appears in
- The reported account name, PFP, and user ID.

![An embed containing a report with the origin, reason, ID, Name, and Mention in an embed](https://cdn.discordapp.com/attachments/1107483500384358510/1181737219971616798/image.png)

## Logs and Alerts
At any point in time, if an alt account Bridge bans was present in your server, an alert will appear in the selected mod channel.

![Embed sent by Bridge warning about a member existing in a server](https://cdn.discordapp.com/attachments/1107483500384358510/1181496658031280179/image.png)

Whenever the list of knowns alts is updated, Bridge runs through every server it is in and verifies that all known alt accounts are banned. 
If a newly added alt is *not* present in a server, the ban will be applied silently. Every time bans are refreshed, Bridge will say so in the log channel, reporting any additions.

![Embed sent by Bridge titled "Ban list reloaded" with the description "46 total entries, 1 new bans in the server"](https://cdn.discordapp.com/attachments/1107483500384358510/1181491748652990535/image.png)

### Invite tracking
When a member joins your server, Bridge will send relevant information about the member in the log channel.
![Invite tracking embed, containing information about account creation date and the invite code used to join.](https://cdn.discordapp.com/attachments/1107483500384358510/1181502520061853776/image.png)

# How to gain access
An instance of Bridge is currently being deployed to RIT communities. Please reach out to **@mae.red** on Discord if you are an admin of an RIT server and would like to add this bot to your server.

## Feature requests
If you already have Bridge in your server and you want it to do more, please consider that this is not a general purpose server bot. If your community needs further cross-server mechanisms, it would best be done seperately. 

## ⟶ developed by [**mae.red**](https://mae.red) and Henry
please consider **[donating](https://www.buymeacoffee.com/maedotred)** to support my efforts!
