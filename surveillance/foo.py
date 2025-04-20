

# @validate_start_end_and_duration
# def create_if_new_else_update(self, chrome_session: ChromeSessionData, right_now: datetime):
#     """This method doesn't use queuing since it needs to check the DB state"""
#     target_domain_name = chrome_session.domain

#     # No need to await this part
#     # TODO: Replace .create_log with a debug table, that records every integer added to a particular log
#     # TODO: ...the table could just be, "here's an id for a certain summary; here's the floats added to make the sum
#     # self.chrome_logging_dao.create_log(chrome_session, right_now)

#     # ### Calculate time difference
#     usage_duration_in_hours = chrome_session.duration.total_seconds() / 3600

#     existing_entry = self.read_row_for_domain(target_domain_name, right_now)
#     print(existing_entry, "49ru")

#     if existing_entry:
#         print("updating hours for " + existing_entry.domain_name)
#         if self.debug:
#             notice_suspicious_durations(existing_entry, chrome_session)
#         self.logger.log_white_multiple("[chrome summary dao] adding time ",
#                                         chrome_session.duration, " to ", target_domain_name)
#         self.update_hours(existing_entry, usage_duration_in_hours)
#     else:
#         today_start = right_now.replace(
#             hour=0, minute=0, second=0, microsecond=0)
#         self._create(target_domain_name, usage_duration_in_hours, today_start)
