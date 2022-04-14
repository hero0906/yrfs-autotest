def del_share(self, target_id, share_id):
    """
    :param target_id:
    :return:
    """
    logger = ""
    target_uri = self.target_uri + "/" + target_id
    # 删除共享权限
    stat, _ = self.delete(target_uri)
    if stat == 202:
        logger.info("Delete target success")
        return True
    else:
        logger.error("Delete target failed.")
        return False
    # 删除share共享：
    share_uri = self.share_uri + "/" + share_id
    stat, _ = self.delete(share_uri)
    if stat == 202:
        logger.info("Delete share success")
        return True
    else:
        logger.error("Delete share failed.")
        return False