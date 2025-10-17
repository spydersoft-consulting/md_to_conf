import logging
import sys
import os
import re
import json
import typing
import mimetypes
import urllib
import requests

LOGGER = logging.getLogger(__name__)


class CheckedResponse(typing.NamedTuple):
    """
    NamedTuple containing page information

    """

    status_code: int
    """ Page Id """

    data: any
    """ Generic object from JSON response """


class PageInfo(typing.NamedTuple):
    """
    NamedTuple containing page information

    """

    id: int
    """ Page Id """

    spaceId: int
    """ Space Id """

    version: int
    """ Page Version """

    link: str
    """ Page Link """


class LabelInfo(typing.NamedTuple):
    """
    NamedTuple containing label information

    """

    id: int
    """ Label Id """

    name: str
    """ The name of the label """

    prefix: str
    """ The prefix of the label """

    label: str
    """ The translated label """


class ConfluenceApiClient:
    def __init__(
        self,
        confluence_api_url: str,
        username: str,
        api_key: str,
        space_key: str,
        editor_version: int,
        use_ssl: bool = True,
    ):
        """
        Constructor

        Args:
            username:  The Confluence user name associated with the API key
            api_key: The API key to access Confluence
            confluence_api_url: The URL to the Confluence site
            space_key: The Key value for the Space for publishing
            editor_version: The editor version for page publishing
            use_ssl:  Whether or not to use SSL.

        """
        self.user_name = username
        self.api_key = api_key
        self.confluence_api_url = confluence_api_url
        self.space_key = space_key
        self.space_id = -1
        self.editor_version = editor_version
        self.use_ssl = use_ssl

    def get_session(self, retry: bool = False, json: bool = True) -> requests.Session:
        """
        Retrieve a `requests` session object

        Args:
            retry: Configure the request with a retry adapter.
            json: Configure the request to set Content-Type to 'application/json'
        Returns:
            requests.Session: A session from the `requests` module

        """
        session = requests.Session()
        if retry:
            retry_max_requests = 5
            retry_backoff_factor = 0.1
            retry_status_forcelist = (404, 500, 501, 502, 503, 504)
            retry = requests.adapters.Retry(
                total=retry_max_requests,
                connect=retry_max_requests,
                read=retry_max_requests,
                backoff_factor=retry_backoff_factor,
                status_forcelist=retry_status_forcelist,
            )
            adapter = requests.adapters.HTTPAdapter(max_retries=retry)
            if self.use_ssl:
                session.mount("https://", adapter)
            else:
                session.mount("http://", adapter)

        session.auth = (self.user_name, self.api_key)
        if json:
            session.headers.update({"Content-Type": "application/json"})
        return session

    def log_not_found(self, object_name: str, log_values: dict[str, str]):
        """
        Write a "not found" message to the LOGGER

        Args:
            object_name: The name to show in the log message
            log_values: Additional key/value pairs to log

        """
        LOGGER.error(f"{object_name} not found.")
        LOGGER.error("Diagnostic Information")
        LOGGER.error(f"\tURL: {self.confluence_api_url}")
        for key in log_values:
            LOGGER.error(f"\t{key}: {log_values[key]}")

    def check_errors_and_get_json(self, response: requests.Response) -> CheckedResponse:
        """
        Check the response for error codes

        Args:
            response : The response from a request

        """
        try:
            response.raise_for_status()
        except requests.RequestException as err:
            LOGGER.debug("err.response: %s", err)
            if response.status_code == 404:
                return CheckedResponse(404, {"error": "Not Found"})
            else:
                LOGGER.error("Error: %d - %s", response.status_code, response.content)
                sys.exit(1)

        return CheckedResponse(response.status_code, response.json())

    def update_page(
        self, page_id: int, title: str, body: str, version: int, parent_id: int
    ):
        """
        Update a page

        Args:
            page_id: confluence page id
            title: confluence page title
            body: confluence page content
            version: confluence page version
            parent_id: confluence parentId
        """
        LOGGER.info("Updating page...")

        url = "%s/api/v2/pages/%d" % (self.confluence_api_url, page_id)

        page_json = {
            "id": page_id,
            "type": "page",
            "title": title,
            "spaceId": "%s" % self.get_space_id(),
            "status": "current",
            "body": {"value": body, "representation": "storage"},
            "version": {"number": version + 1, "minorEdit": True},
            "parentId": "%s" % parent_id,
        }

        session = self.get_session()
        response = self.check_errors_and_get_json(
            session.put(url, data=json.dumps(page_json))
        )

        if response.status_code == 404:
            self.log_not_found("Page", {"Page Id": "%d" % page_id})
            return False

        if response.status_code == 200:
            link = "%s%s" % (self.confluence_api_url, response.data["_links"]["webui"])
            LOGGER.info("Page updated successfully.")
            LOGGER.info("URL: %s", link)
            return True
        else:
            LOGGER.error("Page could not be updated.")

    def get_space_id(self) -> int:
        """
        Retrieve the integer space ID for the current self.space_key

        Returns:
            The integer ID for the space_key of this instance

        """
        if self.space_id > -1:
            return self.space_id

        url = "%s/api/v2/spaces?keys=%s" % (self.confluence_api_url, self.space_key)

        response = self.check_errors_and_get_json(self.get_session().get(url))

        if response.status_code == 404:
            self.log_not_found("Space", {"Space Key": self.space_key})
        else:
            if len(response.data["results"]) >= 1:
                self.space_id = int(response.data["results"][0]["id"])

        return self.space_id

    def create_page(self, title: str, body: str, parent_id: int) -> PageInfo:
        """
        Create a new page

        Args:
            title: confluence page title
            body: confluence page content
            parent_id: confluence parentId

        Returns:
            PageInfo: A num
        """
        LOGGER.info("Creating page...")

        url = "%s/api/v2/pages" % self.confluence_api_url

        space_id = self.get_space_id()

        new_page = {
            "title": title,
            "spaceId": "%d" % space_id,
            "status": "current",
            "body": {"value": body, "representation": "storage"},
            "parentId": "%s" % parent_id
        }

        LOGGER.debug("data: %s", json.dumps(new_page))

        response = self.check_errors_and_get_json(
            self.get_session().post(url, data=json.dumps(new_page))
        )

        if response.status_code == 200:
            data = response.data
            space_id = int(data["spaceId"])
            page_id = int(data["id"])
            version = data["version"]["number"]
            link = "%s%s" % (self.confluence_api_url, data["_links"]["webui"])

            LOGGER.info("Page created in SpaceId %d with ID: %d.", space_id, page_id)
            LOGGER.info("URL: %s", link)

            return PageInfo(page_id, space_id, version, link)
        else:
            LOGGER.error("Could not create page.")
            return PageInfo(0, 0, 0, "")

    def delete_page(self, page_id: int):
        """
        Delete a page

        Args:
            page_id: confluence page id
        """
        LOGGER.info("Deleting page...")
        url = "%s/api/v2/pages/%d" % (self.confluence_api_url, page_id)

        response = self.get_session().delete(url)
        response.raise_for_status()

        if response.status_code == 204:
            LOGGER.info("Page %d deleted successfully.", page_id)
        else:
            LOGGER.error("Page %d could not be deleted.", page_id)

    def get_page(self, title: str) -> PageInfo:
        """
        Retrieve page details by title

        Args:
            title: page title
        Returns:
            Confluence page info
        """

        space_id = self.get_space_id()

        LOGGER.info("\tRetrieving page information: %s", title)
        url = "%s/api/v2/spaces/%d/pages?title=%s" % (
            self.confluence_api_url,
            space_id,
            urllib.parse.quote_plus(title),
        )

        response = self.check_errors_and_get_json(self.get_session(retry=True).get(url))
        if response.status_code == 404:
            self.log_not_found("Page", {"Space Id": "%d" % space_id})
        else:
            data = response.data

            LOGGER.debug("data: %s", str(data))

            if len(data["results"]) >= 1:
                page_id = int(data["results"][0]["id"])
                space_id = int(data["results"][0]["spaceId"])
                version_num = data["results"][0]["version"]["number"]
                link = "%s%s" % (
                    self.confluence_api_url,
                    data["results"][0]["_links"]["webui"],
                )

                page = PageInfo(page_id, space_id, version_num, link)
                return page

        return PageInfo(0, 0, 0, "")

    def get_page_properties(self, page_id: int) -> typing.List[typing.Any]:
        """
        Retrieve page properties by page id

        Args:
            page_id: pageId
        Returns:
            Page Properties Collection
        """

        LOGGER.info("\tRetrieving page property information: %d", page_id)
        url = "%s/api/v2/pages/%d/properties" % (self.confluence_api_url, page_id)

        response = self.check_errors_and_get_json(self.get_session(retry=True).get(url))
        if response.status_code == 404:
            self.log_not_found("Page Properties", {"Page Id": "%d" % page_id})
        else:
            return response.data["results"]

        return []

    def update_page_property(self, page_id: int, page_property) -> bool:
        """
        Update page property by page id

        Args:
            page_id: pageId
        Returns:
            True if successful
        """

        property_json = {
            "page-id": page_id,
            "key": page_property["key"],
            "value": page_property["value"],
            "version": {"number": page_property["version"], "minorEdit": True},
        }

        if "id" in page_property:
            url = "%s/api/v2/pages/%d/properties/%s" % (
                self.confluence_api_url,
                page_id,
                page_property["id"],
            )
            property_json.update({"property-id": page_property["id"]})
            LOGGER.info(
                "Updating Property ID %s on Page %d: %s=%s",
                property_json["property-id"],
                page_id,
                property_json["key"],
                property_json["value"],
            )
            response = self.check_errors_and_get_json(
                self.get_session(retry=True).put(url, data=json.dumps(property_json))
            )
        else:
            url = "%s/api/v2/pages/%d/properties" % (self.confluence_api_url, page_id)
            LOGGER.info(
                "Adding Property to Page %s: %s=%s",
                page_id,
                property_json["key"],
                property_json["value"],
            )
            response = self.check_errors_and_get_json(
                self.get_session(retry=True).post(url, data=json.dumps(property_json))
            )

        if response.status_code != 200:
            LOGGER.error(
                "Unable to add property %s to page %d", property_json["key"], page_id
            )
            return False
        else:
            return True

    def get_attachment(self, page_id: int, filename: str) -> str:
        """
        Get page attachment

        Args:
            page_id: confluence page id
            filename: attachment filename
        Returns:
            The attachment Id, or -1 if not found
        """
        url = "%s/api/v2/pages/%d/attachments?filename=%s" % (
            self.confluence_api_url,
            page_id,
            filename,
        )

        response = self.get_session().get(url)
        response.raise_for_status()
        data = response.json()

        if len(data["results"]) >= 1:
            att_id = data["results"][0]["id"]
            return att_id

        return ""

    def upload_attachment(self, page_id: int, file: str, comment: str) -> bool:
        """
        Upload an attachement

        Args:
            page_id: confluence page id
            file: attachment file
            comment: attachment comment
        Returns:
            True if successful, false otherwise
        """
        if re.search(r"http.*", file):
            return False

        content_type = mimetypes.guess_type(file)[0]
        filename = os.path.basename(file)

        if not os.path.isfile(file):
            LOGGER.error("File %s cannot be found --> skip ", file)
            return False

        file_to_upload = {
            "comment": comment,
            "file": (filename, open(file, "rb"), content_type, {"Expires": "0"}),
        }

        attachment_id = self.get_attachment(page_id, filename)
        if attachment_id != "":
            url = "%s/rest/api/content/%d/child/attachment/%s/data" % (
                self.confluence_api_url,
                page_id,
                attachment_id,
            )
        else:
            url = "%s/rest/api/content/%d/child/attachment/" % (
                self.confluence_api_url,
                page_id,
            )

        session = self.get_session(json=False)
        session.headers.update({"X-Atlassian-Token": "no-check"})

        LOGGER.info("\tUploading attachment %s...", filename)

        response = session.post(url, files=file_to_upload)
        response.raise_for_status()

        return True

    def get_label_info(self, label_name: str) -> LabelInfo:
        """
        Get label information for the given label name

        Args:
            label_name: pageId
        Returns:
            LabelInfo.  If not found, labelInfo will be 0
        """

        LOGGER.debug("\tRetrieving label information: %s", label_name)
        url = "%s/rest/api/label?name=%s" % (
            self.confluence_api_url,
            urllib.parse.quote_plus(label_name),
        )

        response = self.check_errors_and_get_json(self.get_session().get(url))

        if response.status_code == 404:
            label = LabelInfo(0, "", "", "")
        else:
            data = response.data["label"]
            label = LabelInfo(
                int(data["id"]),
                data["name"],
                data["prefix"],
                data["label"],
            )

        return label

    def add_label(self, page_id: int, label_name: str) -> bool:
        """
        Add the given label to the given page Id

        Args:
            page_id: pageId
            label_name: label to be added
        Returns:
            True if successful
        """
        label_info = self.get_label_info(label_name)
        if label_info.id > 0:
            prefix = label_info.prefix
        else:
            prefix = "global"

        add_label_json = {"prefix": prefix, "name": label_name}

        url = "%s/rest/api/content/%d/label" % (self.confluence_api_url, page_id)

        response = self.get_session().post(url, data=json.dumps(add_label_json))
        response.raise_for_status()
        return True

    def update_labels(self, page_id: int, labels: typing.List[str]) -> bool:
        """
        Update labels on given page Id

        Args:
            page_id: pageId
            labels: labels to be added
        Returns:
            True if successful
        """

        LOGGER.info("\tRetrieving page property information: %d", page_id)
        url = "%s/api/v2/pages/%d/labels" % (self.confluence_api_url, page_id)

        response = self.check_errors_and_get_json(self.get_session(retry=True).get(url))
        if response.status_code == 404:
            LOGGER.error(
                "Error: Error finding existing labels. Check the following are correct:"
            )
            LOGGER.error("\tPage Id : %d", page_id)
            LOGGER.error("\tURL: %s", self.confluence_api_url)
            return False

        data = response.data
        for label in labels:
            found = False
            for existing_label in data["results"]:
                if label == existing_label["name"]:
                    found = True

            if not found:
                LOGGER.info("Adding Label '%s' to Page Id %d", label, page_id)
                self.add_label(page_id, label)

            LOGGER.debug("property data: %s", str(data["results"]))

        return data["results"]
