import { Injectable } from '@angular/core';
import jsonData from '../../data/business.json';
//ng g c navigation
@Injectable({
    providedIn: 'root'
})
export class BusinessData {
    pageSize: number = 3;

    getBusinesses(page: number){
        let pageStart = (page - 1) * this.pageSize;
        let pageEnd = pageStart + this.pageSize;
        return jsonData.slice(pageStart, pageEnd);
    }

    getLastPageNumber(){
        return Math.ceil(jsonData.length / this.pageSize);
    }

    getBusiness(id: any){
        let dataToReturn: any[] = [];
        jsonData.forEach(function(business){
            if(business._id.$oid == id){
                dataToReturn.push(business);
            }
        })
        return dataToReturn;
    }
}
