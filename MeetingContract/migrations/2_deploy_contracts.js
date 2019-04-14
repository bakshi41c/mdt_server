var Contract=artifacts.require ("./MeetingContract.sol");
var participants =['0xB0279c67Cfc7f69d14ECb6cb6Ca6dc85AD28c887', '0xA8FAFA79F98Ed1e92Aaf12237F9e23AAe084fe3E', '0x15f38F6F2Ab98f487892314b52759EE4e4Bce22d']
module.exports = function(deployer) {
      deployer.deploy(Contract, 'meetingId', participants);
}