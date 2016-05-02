"""
Authors: Kostas Stamatiou, Donnie Marino

Contact: kostas.stamatiou@digitalglobe.com

Abstraction for the GBDX Ordering interface.
"""

import json
from itertools import izip


class Ordering:

    def __init__(self, interface):
        """Instantiate the GBDX Ordering Interface

        Args:
            interface (Interface): A reference to the GBDX interface.

        Returns:
            An instance of the Ordering interface.

        """
        self.gbdx_connection = interface.gbdx_connection
        self.logger = interface.logger
    
    def order(self, image_catalog_ids, batch_size=100):
        """Orders images from GBDX.

        Args:
            image_catalog_ids (list or string): A list of image catalog ids
            or a single image catalog id.
            batch_size (integer): The image_catalog_ids will be split into batches of batch_size.
            The ordering API max batch size is 100, if batch_size is greater than 100 it will be truncated.

        Returns:
            order_id (list): The list of Ids of orders placed.
        """
        def _order_single_batch(url_, ids, results_list):
            r = self.gbdx_connection.post(url_, data=json.dumps(ids))
            r.raise_for_status()
            order_id = r.json().get("order_id")
            if order_id:
                results_list.append(order_id)

        self.logger.debug('Place order')
        url = 'https://geobigdata.io/orders/v2/order/'

        batch_size = min(100, batch_size)

        sanitized_ids = [id_.strip() for id_ in set(image_catalog_ids) if id_]

        res = []
        # Use itertool batch recipe
        acq_ids_by_batch = izip(*([iter(sanitized_ids)] * batch_size))
        for ids_batch in acq_ids_by_batch:
            _order_single_batch(url, ids_batch, res)

        # Order reminder
        remain_count = len(sanitized_ids) % batch_size
        if remain_count > 0:
            _order_single_batch(url, sanitized_ids[-remain_count:], res)

        return res

    def status(self, order_id):
        """Checks imagery order status. There can be more than one image per
           order and this function returns the status of all images
           within the order.

           Args:
               order_id (str): The ID of the order placed.

           Returns:
               List of dictionaries, one per image. Each dictionary consists
               of the keys 'acquisition_id', 'location' and 'state'.
        """

        self.logger.debug('Get status of order ' + order_id)
        url = 'https://geobigdata.io/orders/v2/order/'
        r = self.gbdx_connection.get(url + order_id)
        r.raise_for_status()
        return r.json().get("acquisitions", {})

